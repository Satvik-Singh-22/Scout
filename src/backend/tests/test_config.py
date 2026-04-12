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
Banquoite — Configuration API Tests

Tests:
  - DB connection registration (role enforcement)
  - Table config CRUD (create, list, update)
  - Role-based access control
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import DatabaseConnection, MasterConfig, Team, User
from backend.tests.conftest import auth_headers


@pytest.mark.asyncio
class TestConnectionRegistration:
    """Tests for POST /config/connections."""

    async def test_create_connection_as_data_owner(
        self, client: AsyncClient, test_data_owner: User
    ):
        """A DATA_OWNER can register a new database connection."""
        response = await client.post(
            "/config/connections",
            headers=auth_headers(test_data_owner),
            json={
                "name": "Production DB",
                "db_type": "POSTGRES",
                "connection_string": "postgresql://user:pass@host/db",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Production DB"
        assert data["db_type"] == "POSTGRES"
        assert "id" in data

    async def test_create_connection_invalid_db_type(
        self, client: AsyncClient, test_data_owner: User
    ):
        """Invalid db_type returns 422."""
        response = await client.post(
            "/config/connections",
            headers=auth_headers(test_data_owner),
            json={
                "name": "Test",
                "db_type": "ORACLE",
                "connection_string": "oracle://...",
            },
        )
        assert response.status_code == 422

    async def test_analyst_cannot_create_connection(
        self, client: AsyncClient, test_analyst: User
    ):
        """An ANALYST is blocked from creating connections."""
        response = await client.post(
            "/config/connections",
            headers=auth_headers(test_analyst),
            json={
                "name": "Should Fail",
                "db_type": "POSTGRES",
                "connection_string": "postgresql://...",
            },
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestTableConfig:
    """Tests for table configuration CRUD."""

    async def test_create_table_config(
        self,
        client: AsyncClient,
        test_data_owner: User,
        async_session: AsyncSession,
        test_team: Team,
    ):
        """A DATA_OWNER can register a table in master_config."""
        # First create a connection
        conn = DatabaseConnection(
            team_id=test_team.id,
            name="Test Connection",
            connection_string_enc="test_conn_string",
            db_type="POSTGRES",
        )
        async_session.add(conn)
        await async_session.commit()
        await async_session.refresh(conn)

        response = await client.post(
            "/config/tables",
            headers=auth_headers(test_data_owner),
            json={
                "db_connection_id": str(conn.id),
                "table_name": "mock_transactions",
                "semantic_definition": "Records of all financial transactions",
                "columns_metadata": [
                    {"name": "id", "type": "UUID", "description": "Primary key"},
                    {"name": "amount", "type": "FLOAT", "description": "Transaction amount"},
                    {"name": "status", "type": "VARCHAR", "description": "SUCCESS or FAILED"},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["table_name"] == "mock_transactions"
        assert data["is_active"] is True
        assert len(data["columns_metadata"]) == 3

    async def test_list_table_configs(
        self,
        client: AsyncClient,
        test_analyst: User,
        async_session: AsyncSession,
        test_team: Team,
    ):
        """Any authenticated user can list their team's table configs."""
        # Seed a connection and config
        conn = DatabaseConnection(
            team_id=test_team.id,
            name="List Test",
            connection_string_enc="test",
            db_type="POSTGRES",
        )
        async_session.add(conn)
        await async_session.flush()

        config = MasterConfig(
            db_connection_id=conn.id,
            team_id=test_team.id,
            table_name="mock_customers",
            semantic_definition="Customer records",
            columns_metadata=[{"name": "id", "type": "UUID", "description": "PK"}],
        )
        async_session.add(config)
        await async_session.commit()

        response = await client.get(
            "/config/tables",
            headers=auth_headers(test_analyst),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(t["table_name"] == "mock_customers" for t in data)

    async def test_update_table_config(
        self,
        client: AsyncClient,
        test_data_owner: User,
        async_session: AsyncSession,
        test_team: Team,
    ):
        """A DATA_OWNER can update is_active and semantic_definition."""
        conn = DatabaseConnection(
            team_id=test_team.id,
            name="Update Test",
            connection_string_enc="test",
            db_type="POSTGRES",
        )
        async_session.add(conn)
        await async_session.flush()

        config = MasterConfig(
            db_connection_id=conn.id,
            team_id=test_team.id,
            table_name="mock_test_table",
            semantic_definition="Original definition",
            columns_metadata=[],
        )
        async_session.add(config)
        await async_session.commit()
        await async_session.refresh(config)

        response = await client.patch(
            f"/config/tables/{config.id}",
            headers=auth_headers(test_data_owner),
            json={
                "is_active": False,
                "semantic_definition": "Updated definition",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["semantic_definition"] == "Updated definition"

    async def test_update_nonexistent_config(
        self, client: AsyncClient, test_data_owner: User
    ):
        """Updating a non-existent config returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(
            f"/config/tables/{fake_id}",
            headers=auth_headers(test_data_owner),
            json={"is_active": False},
        )
        assert response.status_code == 404
