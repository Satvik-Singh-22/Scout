"""
Banquoite — Users API

ELI5 (What does this file do?):
Think of this file as the profile page and directory for employees.
It lets a user ask, "Who am I?" (fetching their own name, role, and settings), 
and lets them update things like whether they want the AI to talk to them like an Executive or a Technical person. 
It also lets them ask, "Who else is on my team?" to see a list of their colleagues and their roles.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.db.models import Team, User, UserTeamAccess
from backend.db.session import get_async_session

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class AccessibleTeam(BaseModel):
    """A team the user has access to."""

    team_id: str
    team_name: str


class UserProfileResponse(BaseModel):
    """Full user profile response including accessible teams."""

    id: str
    email: str
    name: str
    persona: str
    role: str
    team_id: str | None
    accessible_teams: list[AccessibleTeam] = []

    model_config = ConfigDict(from_attributes=True)


class UpdateUserRequest(BaseModel):
    """Request body for updating user profile."""

    persona: str | None = Field(None, pattern="^(EXECUTIVE|TECHNICAL)$")
    name: str | None = Field(None, min_length=1, max_length=255)
    team_id: str | None = None


class UpdateUserResponse(BaseModel):
    """Response after updating user profile."""

    id: str
    email: str
    name: str
    persona: str
    team_id: str | None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# GET /users/me — current user with accessible teams
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Return the authenticated user's profile, including the list of teams
    they have access to (from user_team_access).
    """
    # Fetch accessible teams
    access_result = await db.execute(
        select(UserTeamAccess.team_id, Team.name)
        .join(Team, UserTeamAccess.team_id == Team.id)
        .where(UserTeamAccess.user_id == current_user.id)
    )
    accessible_teams = [
        AccessibleTeam(team_id=str(row[0]), team_name=row[1])
        for row in access_result.fetchall()
    ]

    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        persona=current_user.persona,
        role=current_user.role,
        team_id=str(current_user.team_id) if current_user.team_id else None,
        accessible_teams=accessible_teams,
    )


# ---------------------------------------------------------------------------
# PATCH /users/me — update persona or name
# ---------------------------------------------------------------------------
@router.patch("/me", response_model=UpdateUserResponse)
async def update_me(
    body: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update the authenticated user's persona or name.
    Persona switch (EXECUTIVE ↔ TECHNICAL) changes how the AI formats responses.
    """
    if body.persona is not None:
        current_user.persona = body.persona
    if body.name is not None:
        current_user.name = body.name
    if body.team_id is not None:
        # Validate that the user has access to this team
        access_check = await db.execute(
            select(UserTeamAccess).where(
                UserTeamAccess.user_id == current_user.id,
                UserTeamAccess.team_id == body.team_id
            )
        )
        if not access_check.scalar():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You do not have access to the requested team"
            )
        current_user.team_id = body.team_id

    if body.persona is None and body.name is None and body.team_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field (persona, name, or team_id) must be provided",
        )

    await db.commit()
    await db.refresh(current_user)

    return UpdateUserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        persona=current_user.persona,
        team_id=str(current_user.team_id) if current_user.team_id else None,
    )


# ---------------------------------------------------------------------------
# Pydantic Schema for team members
# ---------------------------------------------------------------------------
class TeamMemberResponse(BaseModel):
    """Response shape for a team member."""

    id: str
    name: str
    email: str
    persona: str
    role: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class TeamInfoResponse(BaseModel):
    """Full team info with members."""

    team_id: str
    team_name: str
    members: list[TeamMemberResponse]


# ---------------------------------------------------------------------------
# GET /users/team — list all members in the current user's team
# ---------------------------------------------------------------------------
@router.get("/team", response_model=TeamInfoResponse)
async def get_team_members(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Return all users belonging to the authenticated user's team.
    Includes name, email, persona, role, and join date.
    """
    if not current_user.team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not assigned to any team",
        )

    # Single query: fetch team name + all members via LEFT JOIN
    result = await db.execute(
        select(User, Team.name.label("team_name"))
        .join(Team, User.team_id == Team.id)
        .where(User.team_id == current_user.team_id)
        .order_by(User.created_at.asc())
    )
    rows = result.all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    # All rows share the same team_name
    team_name = rows[0].team_name

    return TeamInfoResponse(
        team_id=str(current_user.team_id),
        team_name=team_name,
        members=[
            TeamMemberResponse(
                id=str(m.id),
                name=m.name,
                email=m.email,
                persona=m.persona,
                role=m.role,
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
            for m, _ in rows
        ],
    )
