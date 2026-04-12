# Copyright 2026 The SCOUT Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Banquoite — Test Fixtures and Configuration

Uses the real Neon PostgreSQL database (DATABASE_URL from .env).
Tests are skipped if DATABASE_URL is not configured.

Provides:
  - Async PostgreSQL sessions for integration testing
  - Async test client using httpx
  - Pre-seeded test data (team, users, chatroom)
  - Auth helper to generate valid JWT tokens
  - Automatic cleanup of test data after each test
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Load .env before anything else
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from backend.db.models import (
    Base,
    Chatroom,
    Message,
    Team,
    User,
    UserTeamAccess,
)

# ---------------------------------------------------------------------------
# Test Configuration
# ---------------------------------------------------------------------------
TEST_JWT_SECRET = os.getenv("JWT_SECRET", "test-secret-key-minimum-32-characters-long")
TEST_JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Ensure auth modules use the same secret
os.environ["JWT_SECRET"] = TEST_JWT_SECRET
os.environ["JWT_ALGORITHM"] = TEST_JWT_ALGORITHM
os.environ["JWT_EXPIRE_MINUTES"] = os.getenv("JWT_EXPIRE_MINUTES", "60")

# Skip all tests if no DATABASE_URL is configured
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL not configured — set it in backend/.env to run tests against Neon DB",
)

# Unique suffix to identify test data for cleanup
TEST_EMAIL_DOMAIN = "@banquoite-test.dev"

# Unique run ID to avoid email collisions between test runs
_RUN_ID = uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Database Fixtures — real Neon PostgreSQL
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def async_engine():
    """Create an async engine connected to the real Neon PostgreSQL database."""
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create an async session for test operations with automatic cleanup."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

        # Cleanup: remove all test data created during this test
        # Uses raw SQL with proper FK ordering to avoid constraint violations
        try:
            # Delete messages for test users
            await session.execute(text(
                "DELETE FROM messages WHERE chatroom_id IN "
                "(SELECT id FROM chatrooms WHERE user_id IN "
                f"(SELECT id FROM users WHERE email LIKE '%{TEST_EMAIL_DOMAIN}'))"
            ))
            # Delete chatrooms for test users
            await session.execute(text(
                "DELETE FROM chatrooms WHERE user_id IN "
                f"(SELECT id FROM users WHERE email LIKE '%{TEST_EMAIL_DOMAIN}')"
            ))
            # Delete scheduled reports for test users
            await session.execute(text(
                "DELETE FROM scheduled_reports WHERE scheduled_query_id IN "
                "(SELECT id FROM scheduled_queries WHERE user_id IN "
                f"(SELECT id FROM users WHERE email LIKE '%{TEST_EMAIL_DOMAIN}'))"
            ))
            # Delete scheduled queries for test users
            await session.execute(text(
                "DELETE FROM scheduled_queries WHERE user_id IN "
                f"(SELECT id FROM users WHERE email LIKE '%{TEST_EMAIL_DOMAIN}')"
            ))
            # Delete dashboard cards for test users
            await session.execute(text(
                "DELETE FROM dashboard_cards WHERE user_id IN "
                f"(SELECT id FROM users WHERE email LIKE '%{TEST_EMAIL_DOMAIN}')"
            ))
            # Delete user_team_access for test users
            await session.execute(text(
                "DELETE FROM user_team_access WHERE user_id IN "
                f"(SELECT id FROM users WHERE email LIKE '%{TEST_EMAIL_DOMAIN}')"
            ))
            # Delete test users
            await session.execute(text(
                f"DELETE FROM users WHERE email LIKE '%{TEST_EMAIL_DOMAIN}'"
            ))
            # Also clean up non-test-domain emails from registration tests
            await session.execute(text(
                "DELETE FROM user_team_access WHERE user_id IN "
                "(SELECT id FROM users WHERE email LIKE '%@banquoite.dev')"
            ))
            await session.execute(text(
                "DELETE FROM users WHERE email LIKE '%@banquoite.dev'"
            ))
            await session.commit()
        except Exception as exc:
            # Non-fatal: log but don't fail the test
            await session.rollback()
            print(f"Warning: cleanup failed: {exc}")


# ---------------------------------------------------------------------------
# Test Data Fixtures
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def test_team(async_session: AsyncSession):
    """Create a test team."""
    team = Team(name="Test Team A — Payments")
    async_session.add(team)
    await async_session.commit()
    await async_session.refresh(team)
    return team


@pytest_asyncio.fixture
async def test_team_b(async_session: AsyncSession):
    """Create a second test team for cross-team testing."""
    team = Team(name="Test Team B — Operations")
    async_session.add(team)
    await async_session.commit()
    await async_session.refresh(team)
    return team


@pytest_asyncio.fixture
async def test_analyst(async_session: AsyncSession, test_team: Team):
    """Create a test ANALYST user."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        email=f"analyst-{_RUN_ID}{TEST_EMAIL_DOMAIN}",
        name="Test Analyst",
        password_hash=pwd_context.hash("TestPass123!"),
        persona="EXECUTIVE",
        role="ANALYST",
        team_id=test_team.id,
    )
    async_session.add(user)
    await async_session.flush()

    access = UserTeamAccess(user_id=user.id, team_id=test_team.id)
    async_session.add(access)

    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_data_owner(async_session: AsyncSession, test_team: Team):
    """Create a test DATA_OWNER user."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        email=f"owner-{_RUN_ID}{TEST_EMAIL_DOMAIN}",
        name="Test Data Owner",
        password_hash=pwd_context.hash("TestPass123!"),
        persona="TECHNICAL",
        role="DATA_OWNER",
        team_id=test_team.id,
    )
    async_session.add(user)
    await async_session.flush()

    access = UserTeamAccess(user_id=user.id, team_id=test_team.id)
    async_session.add(access)

    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_platform_admin(async_session: AsyncSession):
    """Create a test PLATFORM_ADMIN user (no team)."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        email=f"admin-{_RUN_ID}{TEST_EMAIL_DOMAIN}",
        name="Test Platform Admin",
        password_hash=pwd_context.hash("AdminPass123!"),
        persona="TECHNICAL",
        role="PLATFORM_ADMIN",
        team_id=None,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_enterprise_analyst(
    async_session: AsyncSession, test_team: Team, test_team_b: Team
):
    """Create a test ENTERPRISE_ANALYST with access to two teams."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        email=f"enterprise-{_RUN_ID}{TEST_EMAIL_DOMAIN}",
        name="Test Enterprise Analyst",
        password_hash=pwd_context.hash("TestPass123!"),
        persona="EXECUTIVE",
        role="ENTERPRISE_ANALYST",
        team_id=test_team.id,
    )
    async_session.add(user)
    await async_session.flush()

    for team in [test_team, test_team_b]:
        access = UserTeamAccess(user_id=user.id, team_id=team.id)
        async_session.add(access)

    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_chatroom(async_session: AsyncSession, test_analyst: User):
    """Create a test chatroom for the analyst."""
    chatroom = Chatroom(user_id=test_analyst.id, name="Test Chat")
    async_session.add(chatroom)
    await async_session.commit()
    await async_session.refresh(chatroom)
    return chatroom


# ---------------------------------------------------------------------------
# Auth Helpers
# ---------------------------------------------------------------------------
def create_test_token(user: User) -> str:
    """Generate a JWT token for a test user."""
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "team_id": str(user.team_id) if user.team_id else None,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)


def auth_headers(user: User) -> dict:
    """Return Authorization headers for a test user."""
    return {"Authorization": f"Bearer {create_test_token(user)}"}


# ---------------------------------------------------------------------------
# HTTP Client Fixture
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client(async_session: AsyncSession):
    """
    Create an async HTTP client bound to the FastAPI app with
    the test database session injected.
    """
    from backend.db.session import get_async_session
    from backend.main import app

    async def override_get_async_session():
        yield async_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
