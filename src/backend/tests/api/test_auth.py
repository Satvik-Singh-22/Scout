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
Scout — Authentication API Tests

Tests:
  - User registration (success, validation)
  - User login (success, failure)
  - Current user profile fetching
"""

import pytest
from httpx import AsyncClient
from backend.db.models import User
from backend.tests.conftest import auth_headers

@pytest.mark.asyncio
class TestAuthAPI:
    """Tests for authentication and user profile endpoints."""

    async def test_register_and_me(self, client: AsyncClient):
        """Register a new user and immediately fetch their profile."""
        email = "test-api-auth@banquoite-test.dev"
        password = "SecurePass123!"
        
        # 0. Get a valid team_id
        teams_resp = await client.get("/auth/teams")
        assert teams_resp.status_code == 200
        team_id = teams_resp.json()[0]["id"]
        
        # 1. Register
        reg_resp = await client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "name": "API Test User",
                "persona": "EXECUTIVE",
                "role": "ANALYST",
                "team_id": team_id,
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]

        # 2. Get Profile
        me_resp = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email
        assert me_resp.json()["name"] == "API Test User"

    async def test_login_success(self, client: AsyncClient, test_analyst: User):
        """Test login with existing user credentials."""
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": test_analyst.email,
                "password": "TestPass123!",
            },
        )
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()

    async def test_login_failure(self, client: AsyncClient, test_analyst: User):
        """Test login with incorrect password."""
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": test_analyst.email,
                "password": "WrongPassword123!",
            },
        )
        assert login_resp.status_code == 401

    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that unauthorized requests are blocked."""
        resp = await client.get("/users/me")
        assert resp.status_code == 403
