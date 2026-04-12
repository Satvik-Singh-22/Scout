"""
Banquoite — Dashboard API

ELI5 (What does this file do?):
Think of this file as the manager of your personal bulletin board. 
When you save an important chart or result to look at later, this file organizes it.
Whenever you open your dashboard, this file quickly fetches all your pinned charts 
(up to your latest 20) so you have an instant overview of your important metrics!
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.db.models import DashboardCard, User
from backend.db.session import get_async_session

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class DashboardCardResponse(BaseModel):
    """Response shape for a dashboard card."""

    id: str
    title: str
    query_result: dict
    chart_type: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# GET /dashboard/cards — user's dashboard cards
# ---------------------------------------------------------------------------
@router.get("/cards", response_model=list[DashboardCardResponse])
async def list_dashboard_cards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Return the authenticated user's dashboard cards, ordered by
    creation time (newest first), limited to 20.
    """
    result = await db.execute(
        select(DashboardCard)
        .where(DashboardCard.user_id == current_user.id)
        .order_by(DashboardCard.created_at.desc())
        .limit(20)
    )
    cards = result.scalars().all()

    return [
        DashboardCardResponse(
            id=str(c.id),
            title=c.title,
            query_result=c.query_result,
            chart_type=c.chart_type,
            created_at=c.created_at.isoformat(),
        )
        for c in cards
    ]
