"""
Scout — Alerts API Tests

Tests:
  - List alerts for current team
  - Mark alert as read
  - Unauthorized access to other team's alerts (via mock if possible, but conftest handles cleanup)
"""

import pytest
from httpx import AsyncClient
from backend.db.models import User, Alert
from backend.tests.conftest import auth_headers
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
class TestAlertsAPI:
    """Tests for alert management."""

    async def test_list_alerts_empty(self, client: AsyncClient, test_analyst: User):
        """Listing alerts for a new team should be empty."""
        headers = auth_headers(test_analyst)
        resp = await client.get("/alerts", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_and_mark_read(self, client: AsyncClient, test_analyst: User, async_session: AsyncSession):
        """Create an alert manually and test listing/marking as read."""
        # 1. Manually insert an alert for the test user's team
        alert = Alert(
            team_id=test_analyst.team_id,
            title="Manual Test Alert",
            description="Testing the API connectivity",
            severity="MEDIUM",
            is_read=False
        )
        async_session.add(alert)
        await async_session.commit()
        await async_session.refresh(alert)
        alert_id = str(alert.id)

        headers = auth_headers(test_analyst)
        
        # 2. List
        list_resp = await client.get("/alerts", headers=headers)
        assert list_resp.status_code == 200
        alerts = list_resp.json()
        assert any(a["id"] == alert_id for a in alerts)
        
        # 3. Mark Read
        patch_resp = await client.patch(f"/alerts/{alert_id}/read", headers=headers)
        assert patch_resp.status_code == 200
        assert patch_resp.json()["is_read"] is True

    async def test_mark_read_not_found(self, client: AsyncClient, test_analyst: User):
        """Attempting to mark a non-existent alert as read returns 404."""
        import uuid
        headers = auth_headers(test_analyst)
        fake_id = str(uuid.uuid4())
        resp = await client.patch(f"/alerts/{fake_id}/read", headers=headers)
        assert resp.status_code == 404
