"""
Banquoite — Alerts API

Endpoints:
  GET   /alerts          — return team alerts, ordered by created_at DESC, limit 50
  PATCH /alerts/{id}/read — mark an alert as read
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.db.models import Alert, User
from backend.db.session import get_async_session

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class AlertResponse(BaseModel):
    """Response shape for an alert."""

    id: str
    title: str
    description: str
    severity: str
    data_snapshot: dict | None = None
    is_read: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class MarkReadResponse(BaseModel):
    """Response after marking an alert as read."""

    id: str
    is_read: bool = True


# ---------------------------------------------------------------------------
# GET /alerts — list team alerts
# ---------------------------------------------------------------------------
@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Return all alerts for the authenticated user's team,
    ordered by creation time (newest first), limited to 50.
    """
    if not current_user.team_id:
        return []

    result = await db.execute(
        select(Alert)
        .where(Alert.team_id == current_user.team_id)
        .order_by(Alert.created_at.desc())
        .limit(50)
    )
    alerts = result.scalars().all()

    return [
        AlertResponse(
            id=str(a.id),
            title=a.title,
            description=a.description,
            severity=a.severity,
            data_snapshot=a.data_snapshot,
            is_read=a.is_read,
            created_at=a.created_at.isoformat(),
        )
        for a in alerts
    ]


# ---------------------------------------------------------------------------
# PATCH /alerts/{id}/read — mark alert as read
# ---------------------------------------------------------------------------
@router.patch("/{alert_id}/read", response_model=MarkReadResponse)
async def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Mark a specific alert as read. Only alerts belonging to the user's team can be updated."""
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid alert ID"
        )

    result = await db.execute(select(Alert).where(Alert.id == alert_uuid))
    alert = result.scalar_one_or_none()

    if not alert or alert.team_id != current_user.team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )

    alert.is_read = True
    await db.commit()

    return MarkReadResponse(id=str(alert.id), is_read=True)
