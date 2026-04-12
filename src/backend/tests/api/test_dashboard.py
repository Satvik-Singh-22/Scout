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
Scout — Dashboard API Tests

Tests:
  - List dashboard cards
"""

import pytest
from httpx import AsyncClient
from backend.db.models import User, DashboardCard
from backend.tests.conftest import auth_headers
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
class TestDashboardAPI:
    """Tests for dashboard card retrieval."""

    async def test_list_cards_empty(self, client: AsyncClient, test_analyst: User):
        """Listing cards for a new user should be empty."""
        headers = auth_headers(test_analyst)
        resp = await client.get("/dashboard/cards", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_cards(self, client: AsyncClient, test_analyst: User, async_session: AsyncSession):
        """Create a dashboard card manually and test listing."""
        # 1. Create card
        card = DashboardCard(
            user_id=test_analyst.id,
            title="Revenue Over Month",
            query_result={"total": 50000},
            chart_type="BAR"
        )
        async_session.add(card)
        await async_session.commit()
        await async_session.refresh(card)
        card_id = str(card.id)

        headers = auth_headers(test_analyst)
        
        # 2. List
        resp = await client.get("/dashboard/cards", headers=headers)
        assert resp.status_code == 200
        cards = resp.json()
        assert any(c["id"] == card_id for c in cards)
        assert cards[0]["title"] == "Revenue Over Month"
