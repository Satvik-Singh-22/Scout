"""
Banquoite — Users API

Endpoints:
  GET   /users/me — return current user with accessible teams
  PATCH /users/me — update persona or name
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

    persona: str | None = Field(None, pattern="^(MANAGER|DEVELOPER)$")
    name: str | None = Field(None, min_length=1, max_length=255)


class UpdateUserResponse(BaseModel):
    """Response after updating user profile."""

    id: str
    email: str
    name: str
    persona: str

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
    Persona switch (MANAGER ↔ DEVELOPER) changes how the AI formats responses.
    """
    if body.persona is not None:
        current_user.persona = body.persona
    if body.name is not None:
        current_user.name = body.name

    if body.persona is None and body.name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field (persona or name) must be provided",
        )

    await db.commit()
    await db.refresh(current_user)

    return UpdateUserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        persona=current_user.persona,
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

    # Fetch team name
    team_result = await db.execute(
        select(Team).where(Team.id == current_user.team_id)
    )
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    # Fetch all members in this team
    members_result = await db.execute(
        select(User)
        .where(User.team_id == current_user.team_id)
        .order_by(User.created_at.asc())
    )
    members = members_result.scalars().all()

    return TeamInfoResponse(
        team_id=str(team.id),
        team_name=team.name,
        members=[
            TeamMemberResponse(
                id=str(m.id),
                name=m.name,
                email=m.email,
                persona=m.persona,
                role=m.role,
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
            for m in members
        ],
    )
