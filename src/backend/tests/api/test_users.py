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
Scout — Users API Tests

Tests:
  - Fetch /users/me
  - Update user persona/name
  - Fetch /users/team members
"""

import pytest
from httpx import AsyncClient
from backend.db.models import User
from backend.tests.conftest import auth_headers

@pytest.mark.asyncio
class TestUsersAPI:
    """Tests for user profile and team management."""

    async def test_get_me(self, client: AsyncClient, test_analyst: User):
        """Fetch current user profile and verify fields."""
        headers = auth_headers(test_analyst)
        resp = await client.get("/users/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == test_analyst.email
        assert data["role"] == "ANALYST"
        assert len(data["accessible_teams"]) >= 1

    async def test_update_me(self, client: AsyncClient, test_analyst: User):
        """Update user profile name and persona."""
        headers = auth_headers(test_analyst)
        
        # 1. Update
        patch_resp = await client.patch(
            "/users/me",
            json={"name": "Updated Name", "persona": "TECHNICAL"},
            headers=headers
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["name"] == "Updated Name"
        assert patch_resp.json()["persona"] == "TECHNICAL"

        # 2. Verify
        me_resp = await client.get("/users/me", headers=headers)
        assert me_resp.json()["name"] == "Updated Name"

    async def test_get_team_members(self, client: AsyncClient, test_analyst: User):
        """Fetch team members and verify the current user is present."""
        headers = auth_headers(test_analyst)
        resp = await client.get("/users/team", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "members" in data
        assert any(m["email"] == test_analyst.email for m in data["members"])
        assert data["team_id"] == str(test_analyst.team_id)

    async def test_update_me_validation_error(self, client: AsyncClient, test_analyst: User):
        """Ensure invalid persona returns 422."""
        headers = auth_headers(test_analyst)
        resp = await client.patch(
            "/users/me",
            json={"persona": "INVALID_ROLE"},
            headers=headers
        )
        assert resp.status_code == 422
