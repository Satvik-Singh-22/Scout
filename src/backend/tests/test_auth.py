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
Banquoite — Authentication Tests

Tests:
  - User registration (success, duplicate email, validation)
  - User login (success, wrong password, nonexistent user)
  - JWT token generation and validation
  - Role guard middleware
"""

import pytest
from httpx import AsyncClient

from backend.db.models import User
from backend.tests.conftest import auth_headers


@pytest.mark.asyncio
class TestRegistration:
    """Tests for POST /auth/register."""

    async def test_register_success(self, client: AsyncClient):
        """Registering a new user returns 201 with JWT and user data."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@banquoite.dev",
                "password": "SecurePass123!",
                "name": "New User",
                "persona": "EXECUTIVE",
                "role": "ANALYST",
                "team_name": "New Team",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@banquoite.dev"
        assert data["user"]["name"] == "New User"
        assert data["user"]["persona"] == "EXECUTIVE"
        assert data["user"]["role"] == "ANALYST"

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_analyst: User
    ):
        """Attempting to register with an existing email returns 400."""
        response = await client.post(
            "/auth/register",
            json={
                "email": test_analyst.email,
                "password": "AnotherPass123!",
                "name": "Duplicate",
                "persona": "TECHNICAL",
                "role": "ANALYST",
                "team_name": "Any Team",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_register_invalid_persona(self, client: AsyncClient):
        """Submitting an invalid persona returns 422 validation error."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "invalid@banquoite.dev",
                "password": "SecurePass123!",
                "name": "Bad Persona",
                "persona": "INVALID",
                "role": "ANALYST",
                "team_name": "Some Team",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        """Password shorter than 8 characters returns 422."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "short@banquoite.dev",
                "password": "short",
                "name": "Short Pass",
                "persona": "EXECUTIVE",
                "role": "ANALYST",
                "team_name": "Some Team",
            },
        )
        assert response.status_code == 422

    async def test_register_creates_team_access(self, client: AsyncClient):
        """Registration auto-seeds a UserTeamAccess row for the user."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "access_test@banquoite.dev",
                "password": "SecurePass123!",
                "name": "Access Test",
                "persona": "EXECUTIVE",
                "role": "ANALYST",
                "team_name": "Access Team",
            },
        )
        assert response.status_code == 201
        token = response.json()["access_token"]

        # Verify the user can access /users/me which fetches team access
        me_response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert len(user_data["accessible_teams"]) >= 1


@pytest.mark.asyncio
class TestLogin:
    """Tests for POST /auth/login."""

    async def test_login_success(self, client: AsyncClient, test_analyst: User):
        """Valid credentials return JWT and user data."""
        response = await client.post(
            "/auth/login",
            json={
                "email": test_analyst.email,
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_analyst.email

    async def test_login_wrong_password(self, client: AsyncClient, test_analyst: User):
        """Incorrect password returns 401."""
        response = await client.post(
            "/auth/login",
            json={
                "email": test_analyst.email,
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Login with a non-registered email returns 401."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "noone@banquoite.dev",
                "password": "SomePass123!",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAuthMiddleware:
    """Tests for authentication middleware and role guards."""

    async def test_unauthenticated_request(self, client: AsyncClient):
        """Requests without a Bearer token return 403."""
        response = await client.get("/users/me")
        assert response.status_code == 403

    async def test_invalid_token(self, client: AsyncClient):
        """Requests with an invalid JWT return 401."""
        response = await client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_valid_token_returns_user(
        self, client: AsyncClient, test_analyst: User
    ):
        """A valid JWT returns the user profile."""
        response = await client.get(
            "/users/me",
            headers=auth_headers(test_analyst),
        )
        assert response.status_code == 200
        assert response.json()["email"] == test_analyst.email

    async def test_data_owner_guard_blocks_analyst(
        self, client: AsyncClient, test_analyst: User
    ):
        """An ANALYST cannot access DATA_OWNER-only endpoints."""
        response = await client.post(
            "/config/connections",
            headers=auth_headers(test_analyst),
            json={
                "name": "Test",
                "db_type": "POSTGRES",
                "connection_string": "postgres://...",
            },
        )
        assert response.status_code == 403

    async def test_platform_admin_guard_blocks_analyst(
        self, client: AsyncClient, test_analyst: User
    ):
        """An ANALYST cannot access PLATFORM_ADMIN-only endpoints."""
        response = await client.get(
            "/admin/tables",
            headers=auth_headers(test_analyst),
        )
        assert response.status_code == 403
