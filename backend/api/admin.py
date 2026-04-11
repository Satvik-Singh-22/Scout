"""
Banquoite — Platform Admin API

Governance endpoints for PLATFORM_ADMIN users. Controls table assignments
to teams, cross-team access grants, and provides full estate visibility.

Endpoints:
  GET   /admin/tables                   — all mock tables with team assignments
  GET   /admin/teams                    — team list with table & member counts
  POST  /admin/assign                   — assign tables to a team
  PATCH /admin/revoke/{config_id}       — deactivate a master_config row
  GET   /admin/users                    — all users with access info
  POST  /admin/users/{user_id}/access   — replace user_team_access rows
"""

import uuid
import logging
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text, func, delete, case
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import require_platform_admin
from backend.db.models import (
    DatabaseConnection,
    MasterConfig,
    Team,
    User,
    UserTeamAccess,
)
from backend.db.session import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class TeamAssignment(BaseModel):
    """A team's assignment for a specific table."""

    config_id: str
    team_id: str
    team_name: str
    is_active: bool


class AdminTableResponse(BaseModel):
    """Response for a mock table with its team assignments."""

    table_name: str
    column_count: int
    team_assignments: list[TeamAssignment] = []


class TeamSummary(BaseModel):
    """Response for a team summary."""

    id: str
    name: str
    table_count: int
    member_count: int


class TableAssignmentInput(BaseModel):
    """Input for a single table assignment."""

    table_name: str
    semantic_definition: str
    columns_metadata: list[dict]


class AssignRequest(BaseModel):
    """Request body for assigning tables to a team."""

    team_id: str
    table_assignments: list[TableAssignmentInput]


class AssignResponse(BaseModel):
    """Response after assigning tables."""

    assigned_count: int
    team_id: str


class RevokeResponse(BaseModel):
    """Response after revoking a master_config entry."""

    id: str
    is_active: bool = False


class AccessibleTeam(BaseModel):
    """A team that a user can access."""

    team_id: str
    team_name: str


class AdminUserResponse(BaseModel):
    """Response for a user with access info."""

    id: str
    name: str
    email: str
    role: str
    team_id: str | None
    team_name: str | None
    accessible_teams: list[AccessibleTeam] = []


class SetAccessRequest(BaseModel):
    """Request body for replacing user_team_access rows."""

    team_ids: list[str]


class SetAccessResponse(BaseModel):
    """Response after updating user access."""

    user_id: str
    accessible_teams: list[AccessibleTeam]


# ---------------------------------------------------------------------------
# GET /admin/tables — all mock tables with team assignments
# ---------------------------------------------------------------------------
@router.get("/tables", response_model=list[AdminTableResponse])
async def list_all_tables(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Return all mock_ tables in the database with their current team assignments.
    The PLATFORM_ADMIN sees the full estate across all teams.
    """
    # Fetch all mock_ tables from INFORMATION_SCHEMA
    scan_result = await db.execute(
        text("""
            SELECT t.table_name,
                   (SELECT COUNT(*)
                    FROM information_schema.columns c
                    WHERE c.table_name = t.table_name
                      AND c.table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE t.table_schema = 'public'
              AND t.table_name LIKE 'mock_%'
            ORDER BY t.table_name
        """)
    )
    mock_tables = scan_result.fetchall()

    # Fetch all master_config entries with team info
    config_result = await db.execute(
        select(MasterConfig, Team.name.label("team_name"))
        .join(Team, MasterConfig.team_id == Team.id)
    )
    config_rows = config_result.all()

    # Build a lookup: table_name -> list of team assignments
    assignments_map: dict[str, list[TeamAssignment]] = {}
    for config, team_name in config_rows:
        if config.table_name not in assignments_map:
            assignments_map[config.table_name] = []
        assignments_map[config.table_name].append(
            TeamAssignment(
                config_id=str(config.id),
                team_id=str(config.team_id),
                team_name=team_name,
                is_active=config.is_active,
            )
        )

    return [
        AdminTableResponse(
            table_name=row[0],
            column_count=row[1],
            team_assignments=assignments_map.get(row[0], []),
        )
        for row in mock_tables
    ]


# ---------------------------------------------------------------------------
# GET /admin/teams — team list with counts
# ---------------------------------------------------------------------------
@router.get("/teams", response_model=list[TeamSummary])
async def list_teams(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """Return all teams with their table and member counts.

    Uses a single aggregated query with LEFT JOINs instead of N+1 queries.
    """
    # Single query: count active tables and members per team via LEFT JOINs
    stmt = (
        select(
            Team.id,
            Team.name,
            func.count(
                func.distinct(
                    case(
                        (MasterConfig.is_active == True, MasterConfig.id),
                        else_=None,
                    )
                )
            ).label("table_count"),
            func.count(func.distinct(User.id)).label("member_count"),
        )
        .outerjoin(MasterConfig, (MasterConfig.team_id == Team.id))
        .outerjoin(User, User.team_id == Team.id)
        .group_by(Team.id, Team.name)
        .order_by(Team.name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        TeamSummary(
            id=str(row.id),
            name=row.name,
            table_count=row.table_count,
            member_count=row.member_count,
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# POST /admin/assign — assign tables to a team
# ---------------------------------------------------------------------------
@router.post("/assign", response_model=AssignResponse)
async def assign_tables(
    body: AssignRequest,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create master_config rows for the given team, making those tables
    accessible to the team's pipeline.

    Uses a hardcoded/demo db_connection_id for the hackathon. In production,
    this would reference real registered connections.
    """
    try:
        team_uuid = uuid.UUID(body.team_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid team_id"
        )

    # Verify team exists
    team_result = await db.execute(select(Team).where(Team.id == team_uuid))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )

    # Find or create a demo database connection for this team
    conn_result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.team_id == team_uuid).limit(1)
    )
    db_conn = conn_result.scalar_one_or_none()

    if not db_conn:
        # Create a demo connection for the team
        db_conn = DatabaseConnection(
            team_id=team_uuid,
            name=f"Demo Connection - {team.name}",
            connection_string_enc="demo_connection",
            db_type="POSTGRES",
        )
        db.add(db_conn)
        await db.flush()

    assigned_count = 0

    # We will need the LLM components for meaning generation
    from backend.agents.llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    for assignment in body.table_assignments:
        # Check if this table is already assigned to this team
        existing = await db.execute(
            select(MasterConfig).where(
                MasterConfig.team_id == team_uuid,
                MasterConfig.table_name == assignment.table_name,
            )
        )
        existing_config = existing.scalar_one_or_none()

        # Decide if we need to generate semantic_definition via Groq
        # The frontend provides a default pattern 'Data from X table.'
        final_semantic = assignment.semantic_definition
        is_default = final_semantic.startswith("Data from") and final_semantic.endswith("table.")
        
        if is_default or not final_semantic:
            try:
                # 1. Fetch schema for this table
                schema_query = await db.execute(
                    text("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = :t_name
                          AND table_schema = 'public'
                    """),
                    {"t_name": assignment.table_name}
                )
                columns = schema_query.fetchall()
                if columns:
                    schema_str = "\n".join([f"- {col[0]} ({col[1]})" for col in columns])
                    
                    # 2. Call LLM for generation
                    llm = get_llm(temperature=0.3)
                    prompt = f"Given the database table '{assignment.table_name}' with the following columns:\n{schema_str}\n\nWhat is the business purpose of this table? Provide a 1-3 sentence detailed yet concise professional explanation."
                    
                    logger.info(f"Generating purpose for table {assignment.table_name} via LLM")
                    res = await llm.ainvoke([
                        SystemMessage(content="You are an expert data architect. You provide highly accurate, concise semantics for database tables."),
                        HumanMessage(content=prompt)
                    ])
                    final_semantic = res.content.strip()
            except Exception as e:
                logger.error(f"Error generating purpose for {assignment.table_name}: {e}")
                # Keep the fallback `final_semantic`

        if existing_config:
            # Re-activate if it was deactivated
            existing_config.is_active = True
            existing_config.semantic_definition = final_semantic
            existing_config.columns_metadata = assignment.columns_metadata
        else:
            config = MasterConfig(
                db_connection_id=db_conn.id,
                team_id=team_uuid,
                table_name=assignment.table_name,
                semantic_definition=final_semantic,
                columns_metadata=assignment.columns_metadata,
            )
            db.add(config)

        assigned_count += 1

    await db.commit()

    return AssignResponse(assigned_count=assigned_count, team_id=body.team_id)


# ---------------------------------------------------------------------------
# PATCH /admin/revoke/{master_config_id} — deactivate a config row
# ---------------------------------------------------------------------------
@router.patch("/revoke/{config_id}", response_model=RevokeResponse)
async def revoke_table_access(
    config_id: str,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Set is_active=FALSE on a master_config row, immediately removing the table
    from the team's pipeline scope.
    """
    try:
        config_uuid = uuid.UUID(config_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid config ID"
        )

    result = await db.execute(
        select(MasterConfig).where(MasterConfig.id == config_uuid)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master config entry not found",
        )

    config.is_active = False
    await db.commit()

    return RevokeResponse(id=str(config.id), is_active=False)


# ---------------------------------------------------------------------------
# GET /admin/users — all users with access info
# ---------------------------------------------------------------------------
@router.get("/users", response_model=list[AdminUserResponse])
async def list_all_users(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """Return all users with their team and cross-team access information.

    Uses 2 queries total instead of 2*N+1 (one for users+team, one for all access rows).
    """
    # Query 1: All users with their team name via LEFT JOIN
    TeamAlias = aliased(Team)
    user_stmt = (
        select(User, TeamAlias.name.label("team_name"))
        .outerjoin(TeamAlias, User.team_id == TeamAlias.id)
        .order_by(User.created_at.desc())
    )
    user_result = await db.execute(user_stmt)
    user_rows = user_result.all()

    # Query 2: All access rows for ALL users in a single batch
    access_stmt = (
        select(
            UserTeamAccess.user_id,
            UserTeamAccess.team_id,
            Team.name.label("team_name"),
        )
        .join(Team, UserTeamAccess.team_id == Team.id)
    )
    access_result = await db.execute(access_stmt)
    access_rows = access_result.all()

    # Build lookup: user_id -> list of AccessibleTeam
    access_map: dict[uuid.UUID, list[AccessibleTeam]] = defaultdict(list)
    for row in access_rows:
        access_map[row.user_id].append(
            AccessibleTeam(team_id=str(row.team_id), team_name=row.team_name)
        )

    return [
        AdminUserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            team_id=str(user.team_id) if user.team_id else None,
            team_name=team_name,
            accessible_teams=access_map.get(user.id, []),
        )
        for user, team_name in user_rows
    ]


# ---------------------------------------------------------------------------
# POST /admin/users/{user_id}/access — replace user_team_access rows
# ---------------------------------------------------------------------------
@router.post("/users/{user_id}/access", response_model=SetAccessResponse)
async def set_user_access(
    user_id: str,
    body: SetAccessRequest,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Replace all user_team_access rows for the specified user.
    Used to grant or revoke cross-team access for ENTERPRISE_ANALYST users.
    """
    try:
        target_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user_id"
        )

    # Verify target user exists
    user_result = await db.execute(select(User).where(User.id == target_uuid))
    target_user = user_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Delete existing access rows for this user
    await db.execute(
        delete(UserTeamAccess).where(UserTeamAccess.user_id == target_uuid)
    )

    # Create new access rows
    accessible_teams = []
    for team_id_str in body.team_ids:
        try:
            team_uuid = uuid.UUID(team_id_str)
        except ValueError:
            continue

        # Verify team exists
        team_result = await db.execute(select(Team).where(Team.id == team_uuid))
        team = team_result.scalar_one_or_none()
        if not team:
            continue

        access = UserTeamAccess(
            user_id=target_uuid,
            team_id=team_uuid,
            granted_by=current_user.id,
        )
        db.add(access)
        accessible_teams.append(
            AccessibleTeam(team_id=str(team.id), team_name=team.name)
        )

    await db.commit()

    return SetAccessResponse(
        user_id=user_id,
        accessible_teams=accessible_teams,
    )
