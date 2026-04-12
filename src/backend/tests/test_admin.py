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
Banquoite — Admin API Tests

Tests:
  - Platform admin role guard enforcement
  - Team listing
  - User listing with access info
  - Cross-team access grant/revoke
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Team, User, UserTeamAccess
from backend.tests.conftest import auth_headers


@pytest.mark.asyncio
class TestAdminRoleGuard:
    """Tests for PLATFORM_ADMIN role guard enforcement."""

    async def test_analyst_blocked_from_admin_tables(
        self, client: AsyncClient, test_analyst: User
    ):
        """An ANALYST cannot access /admin/tables."""
        response = await client.get(
            "/admin/tables",
            headers=auth_headers(test_analyst),
        )
        assert response.status_code == 403

    async def test_data_owner_blocked_from_admin_tables(
        self, client: AsyncClient, test_data_owner: User
    ):
        """A DATA_OWNER cannot access /admin/tables."""
        response = await client.get(
            "/admin/tables",
            headers=auth_headers(test_data_owner),
        )
        assert response.status_code == 403

    async def test_admin_can_access_admin_tables(
        self, client: AsyncClient, test_platform_admin: User
    ):
        """A PLATFORM_ADMIN can access /admin/tables."""
        response = await client.get(
            "/admin/tables",
            headers=auth_headers(test_platform_admin),
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestAdminTeams:
    """Tests for GET /admin/teams."""

    async def test_list_teams(
        self, client: AsyncClient, test_platform_admin: User, test_team: Team
    ):
        """Admin can list all teams with table and member counts."""
        response = await client.get(
            "/admin/teams",
            headers=auth_headers(test_platform_admin),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        team_entry = next(
            (t for t in data if t["id"] == str(test_team.id)), None
        )
        assert team_entry is not None
        assert team_entry["name"] == test_team.name
        assert "table_count" in team_entry
        assert "member_count" in team_entry


@pytest.mark.asyncio
class TestAdminUsers:
    """Tests for GET /admin/users."""

    async def test_list_users(
        self,
        client: AsyncClient,
        test_platform_admin: User,
        test_analyst: User,
    ):
        """Admin can list all users with access info."""
        response = await client.get(
            "/admin/users",
            headers=auth_headers(test_platform_admin),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # admin + analyst at minimum

        analyst_entry = next(
            (u for u in data if u["email"] == test_analyst.email), None
        )
        assert analyst_entry is not None
        assert analyst_entry["role"] == "ANALYST"
        assert "accessible_teams" in analyst_entry


@pytest.mark.asyncio
class TestAdminAccessManagement:
    """Tests for POST /admin/users/{user_id}/access."""

    async def test_grant_cross_team_access(
        self,
        client: AsyncClient,
        test_platform_admin: User,
        test_analyst: User,
        test_team: Team,
        test_team_b: Team,
    ):
        """Admin can grant an analyst access to multiple teams."""
        response = await client.post(
            f"/admin/users/{test_analyst.id}/access",
            headers=auth_headers(test_platform_admin),
            json={"team_ids": [str(test_team.id), str(test_team_b.id)]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_analyst.id)
        assert len(data["accessible_teams"]) == 2

    async def test_revoke_cross_team_access(
        self,
        client: AsyncClient,
        test_platform_admin: User,
        test_enterprise_analyst: User,
        test_team: Team,
    ):
        """Admin can revoke cross-team access by setting only one team."""
        response = await client.post(
            f"/admin/users/{test_enterprise_analyst.id}/access",
            headers=auth_headers(test_platform_admin),
            json={"team_ids": [str(test_team.id)]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["accessible_teams"]) == 1
        assert data["accessible_teams"][0]["team_id"] == str(test_team.id)

    async def test_set_access_invalid_user(
        self, client: AsyncClient, test_platform_admin: User, test_team: Team
    ):
        """Setting access for a nonexistent user returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.post(
            f"/admin/users/{fake_id}/access",
            headers=auth_headers(test_platform_admin),
            json={"team_ids": [str(test_team.id)]},
        )
        assert response.status_code == 404

    async def test_assign_tables_to_team(
        self,
        client: AsyncClient,
        test_platform_admin: User,
        test_team: Team,
    ):
        """Admin can assign tables to a team via /admin/assign."""
        response = await client.post(
            "/admin/assign",
            headers=auth_headers(test_platform_admin),
            json={
                "team_id": str(test_team.id),
                "table_assignments": [
                    {
                        "table_name": "mock_transactions",
                        "semantic_definition": "Financial transactions data",
                        "columns_metadata": [
                            {"name": "id", "type": "UUID", "description": "PK"},
                            {"name": "amount", "type": "FLOAT", "description": "Amount"},
                        ],
                    }
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_count"] == 1
        assert data["team_id"] == str(test_team.id)
