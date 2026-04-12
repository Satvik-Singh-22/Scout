"""
Scout — Authentication & Authorization

Endpoints:
  POST /auth/register — create a new user account
  POST /auth/login    — authenticate and receive JWT

Dependencies (reused across all routes):
  get_current_user()      — decode JWT, return User object
  require_data_owner()    — enforce DATA_OWNER role
  require_platform_admin() — enforce PLATFORM_ADMIN role
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Team, User, UserTeamAccess
from backend.db.session import get_async_session

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    name: str = Field(..., min_length=1, max_length=255)
    persona: str = Field(..., pattern="^(MANAGER|DEVELOPER)$")
    role: str = Field(
        default="ANALYST",
        pattern="^(DATA_OWNER|ANALYST|ENTERPRISE_ANALYST)$",
    )
    team_id: str = Field(..., description="UUID of the team to join")


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User data returned in auth responses."""

    id: str
    email: str
    name: str
    persona: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Unified response for both register and login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def _create_access_token(user: User) -> str:
    """
    Generate a JWT containing user identity claims.
    Expires after JWT_EXPIRE_MINUTES (default 24 hours).
    """
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "team_id": str(user.team_id) if user.team_id else None,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/teams")
async def list_teams(
    db: AsyncSession = Depends(get_async_session),
):
    """List all available teams (public — no auth required)."""
    result = await db.execute(select(Team).order_by(Team.name))
    teams = result.scalars().all()
    return [
        {"id": str(t.id), "name": t.name}
        for t in teams
    ]


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new user account.

    1. Check email uniqueness
    2. Validate team_id exists
    3. Create User with hashed password
    4. Seed a UserTeamAccess row (own team access)
    5. Return JWT + user data
    """
    # Check for duplicate email
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    # Validate team exists
    try:
        team_uuid = uuid.UUID(body.team_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid team ID format",
        )
    team_result = await db.execute(select(Team).where(Team.id == team_uuid))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team not found",
        )

    # Create user
    user = User(
        email=body.email,
        name=body.name,
        password_hash=_hash_password(body.password),
        persona=body.persona,
        role=body.role,
        team_id=team.id,
    )
    db.add(user)
    await db.flush()  # Get user.id

    # Seed own-team access in user_team_access
    access = UserTeamAccess(
        user_id=user.id,
        team_id=team.id,
    )
    db.add(access)
    await db.commit()
    await db.refresh(user)

    token = _create_access_token(user)
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            persona=user.persona,
            role=user.role,
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Authenticate a user and return a JWT.

    1. Find user by email
    2. Verify password
    3. Return JWT + user data
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not _verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = _create_access_token(user)
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            persona=user.persona,
            role=user.role,
        ),
    )


# ---------------------------------------------------------------------------
# Auth Dependencies — reused across all route modules
# ---------------------------------------------------------------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Decode the Bearer JWT and return the authenticated User object.
    Raises HTTP 401 on invalid or expired tokens.
    """
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(exc)}",
        )

    # Fetch user from database — validates the user still exists
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: malformed user ID",
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found — account may have been deleted",
        )

    return user


async def require_data_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce that the authenticated user has the DATA_OWNER role."""
    if current_user.role != "DATA_OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data Owner role required",
        )
    return current_user


async def require_platform_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce that the authenticated user has the PLATFORM_ADMIN role."""
    if current_user.role != "PLATFORM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform Admin role required",
        )
    return current_user
