"""
Scout — Scheduled Queries API Tests

Tests:
  - Create scheduled query
  - List scheduled queries
  - Update and delete scheduled query
  - Fetch execution history
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import User
from backend.tests.conftest import auth_headers

@pytest.mark.asyncio
class TestScheduledAPI:
    """Tests for scheduled query management."""

    async def test_create_and_list_scheduled(self, client: AsyncClient, test_analyst: User):
        """Create a scheduled query and verify it appears in the list."""
        headers = auth_headers(test_analyst)
        
        # 1. Create
        payload = {
            "query_text": "SELECT COUNT(*) FROM mock_transactions",
            "cron_expression": "0 12 * * *",  # Every day at noon
            "delivery": "EMAIL",
            "delivery_email": test_analyst.email,
            "alert_condition": "Notify me if count > 0",
            "alert_severity": "HIGH"
        }
        create_resp = await client.post("/scheduled", json=payload, headers=headers)
        assert create_resp.status_code == 201
        query_id = create_resp.json()["id"]

        # 2. List
        list_resp = await client.get("/scheduled", headers=headers)
        assert list_resp.status_code == 200
        queries = list_resp.json()
        assert any(q["id"] == query_id for q in queries)

    async def test_update_scheduled(self, client: AsyncClient, test_analyst: User):
        """Update an existing scheduled query's status."""
        headers = auth_headers(test_analyst)
        
        # Create first
        payload = {
            "query_text": "SELECT 1",
            "cron_expression": "0 0 * * *",
            "delivery": "DASHBOARD"
        }
        create_resp = await client.post("/scheduled", json=payload, headers=headers)
        query_id = create_resp.json()["id"]

        # Update (deactivate)
        patch_resp = await client.patch(
            f"/scheduled/{query_id}",
            json={"is_active": False},
            headers=headers
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["is_active"] is False

    async def test_delete_scheduled(self, client: AsyncClient, test_analyst: User):
        """Register, create, and then delete a scheduled query."""
        headers = auth_headers(test_analyst)
        
        # Create
        create_resp = await client.post(
            "/scheduled",
            json={"query_text": "DELETE ME", "cron_expression": "* * * * *", "delivery": "DASHBOARD"},
            headers=headers
        )
        query_id = create_resp.json()["id"]

        # Delete
        del_resp = await client.delete(f"/scheduled/{query_id}", headers=headers)
        assert del_resp.status_code == 204

        # Verify gone
        list_resp = await client.get("/scheduled", headers=headers)
        assert not any(q["id"] == query_id for q in list_resp.json())

    async def test_invalid_cron(self, client: AsyncClient, test_analyst: User):
        """Ensure invalid cron expressions return 400."""
        headers = auth_headers(test_analyst)
        payload = {
            "query_text": "SELECT 1",
            "cron_expression": "invalid cron",
            "delivery": "DASHBOARD"
        }
        resp = await client.post("/scheduled", json=payload, headers=headers)
        assert resp.status_code == 400
        assert "Invalid cron" in resp.json()["detail"]

    async def test_get_scheduled_history(self, client: AsyncClient, test_analyst: User, async_session: AsyncSession):
        """Manually insert a report and verify it appears in history."""
        from backend.db.models import ScheduledQuery, ScheduledReport
        import uuid

        headers = auth_headers(test_analyst)
        
        # 1. Create a query
        sq = ScheduledQuery(
            user_id=test_analyst.id,
            query_text="History Test",
            cron_expression="0 0 * * *",
            delivery="DASHBOARD"
        )
        async_session.add(sq)
        await async_session.commit()
        await async_session.refresh(sq)

        # 2. Create a report for it
        report = ScheduledReport(
            scheduled_query_id=sq.id,
            status="SUCCESS",
            result_data={"answer": "42"}
        )
        async_session.add(report)
        await async_session.commit()

        # 3. Fetch history
        resp = await client.get(f"/scheduled/{sq.id}/history", headers=headers)
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) >= 1
        assert history[0]["status"] == "SUCCESS"
        assert history[0]["result_data"]["answer"] == "42"
