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
Banquoite — Scheduled Queries API

ELI5 (What does this file do?):
Think of this file as a smart alarm clock for data!
Instead of running a report manually every Monday morning, a user can tell this file to do it for them.
It takes a query, looks at the schedule rule (like "every Monday at 9 AM"), and saves it. 
It also tracks the history—letting you see all the past times the alarm went off and what the results were.
"""

import uuid
from datetime import datetime, timezone

from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.db.models import ScheduledQuery, ScheduledReport, User
from backend.db.session import get_async_session

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class CreateScheduledRequest(BaseModel):
    """Request body for creating a scheduled query."""

    query_text: str = Field(..., min_length=1, max_length=5000)
    cron_expression: str = Field(
        ..., min_length=1, max_length=100,
        description="Cron expression (e.g. '0 9 * * 1' for every Monday at 9 AM)"
    )
    delivery: str = Field(..., pattern="^(EMAIL|DASHBOARD)$")
    delivery_email: str | None = None
    alert_condition: str | None = Field(
        None, max_length=1000,
        description="English-text alert condition (e.g. 'Alert me if failure rate exceeds 5%')"
    )
    alert_severity: str | None = Field(
        "MEDIUM", pattern="^(HIGH|MEDIUM|LOW)$",
        description="Alert severity when condition triggers"
    )


class ScheduledQueryResponse(BaseModel):
    """Response shape for a scheduled query."""

    id: str
    query_text: str
    cron_expression: str
    delivery: str
    is_active: bool
    alert_condition: str | None = None
    alert_severity: str | None = None
    last_run_at: str | None = None
    next_run_at: str | None = None
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UpdateScheduledRequest(BaseModel):
    """Request body for updating a scheduled query. All fields optional."""

    query_text: str | None = None
    cron_expression: str | None = None
    delivery: str | None = Field(None, pattern="^(EMAIL|DASHBOARD)$")
    delivery_email: str | None = None
    is_active: bool | None = None
    alert_condition: str | None = None
    alert_severity: str | None = Field(None, pattern="^(HIGH|MEDIUM|LOW)$")


class ScheduledReportResponse(BaseModel):
    """Response shape for a scheduled report execution."""

    id: str
    status: str
    result_data: dict
    executed_at: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _compute_next_run(cron_expression: str) -> datetime | None:
    """
    Compute the next run time from a cron expression using APScheduler's CronTrigger.
    Returns None if the expression is invalid.
    """
    try:
        # Parse the cron expression (5-field: minute hour day month day_of_week)
        parts = cron_expression.strip().split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )
        elif len(parts) == 6:
            trigger = CronTrigger(
                second=parts[0],
                minute=parts[1],
                hour=parts[2],
                day=parts[3],
                month=parts[4],
                day_of_week=parts[5],
            )
        else:
            return None

        now = datetime.now(timezone.utc)
        next_fire = trigger.get_next_fire_time(None, now)
        return next_fire
    except Exception:
        return None


# ---------------------------------------------------------------------------
# GET /scheduled — list user's scheduled queries
# ---------------------------------------------------------------------------
@router.get("", response_model=list[ScheduledQueryResponse])
async def list_scheduled_queries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Return all scheduled queries belonging to the authenticated user."""
    result = await db.execute(
        select(ScheduledQuery)
        .where(ScheduledQuery.user_id == current_user.id)
        .order_by(ScheduledQuery.created_at.desc())
    )
    queries = result.scalars().all()

    return [
        ScheduledQueryResponse(
            id=str(q.id),
            query_text=q.query_text,
            cron_expression=q.cron_expression,
            delivery=q.delivery,
            is_active=q.is_active,
            alert_condition=q.alert_condition,
            alert_severity=q.alert_severity,
            last_run_at=q.last_run_at.isoformat() if q.last_run_at else None,
            next_run_at=q.next_run_at.isoformat() if q.next_run_at else None,
            created_at=q.created_at.isoformat() if q.created_at else None,
        )
        for q in queries
    ]


# ---------------------------------------------------------------------------
# POST /scheduled — create a new scheduled query
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=ScheduledQueryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scheduled_query(
    body: CreateScheduledRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new scheduled query. Computes next_run_at from the cron expression.
    """
    # Validate cron expression by computing next run
    next_run = _compute_next_run(body.cron_expression)
    if next_run is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cron expression. Use 5-field format: minute hour day month day_of_week",
        )

    # Validate delivery email if delivery is EMAIL
    if body.delivery == "EMAIL" and not body.delivery_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="delivery_email is required when delivery is EMAIL",
        )

    query = ScheduledQuery(
        user_id=current_user.id,
        query_text=body.query_text,
        cron_expression=body.cron_expression,
        delivery=body.delivery,
        delivery_email=body.delivery_email,
        alert_condition=body.alert_condition,
        alert_severity=body.alert_severity or "MEDIUM",
        next_run_at=next_run,
    )
    db.add(query)
    await db.commit()
    await db.refresh(query)

    return ScheduledQueryResponse(
        id=str(query.id),
        query_text=query.query_text,
        cron_expression=query.cron_expression,
        delivery=query.delivery,
        is_active=query.is_active,
        alert_condition=query.alert_condition,
        alert_severity=query.alert_severity,
        next_run_at=query.next_run_at.isoformat() if query.next_run_at else None,
        created_at=query.created_at.isoformat() if query.created_at else None,
    )


# ---------------------------------------------------------------------------
# PATCH /scheduled/{id} — update scheduled query fields
# ---------------------------------------------------------------------------
@router.patch("/{query_id}", response_model=ScheduledQueryResponse)
async def update_scheduled_query(
    query_id: str,
    body: UpdateScheduledRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Update a scheduled query. All fields are optional."""
    try:
        query_uuid = uuid.UUID(query_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid query ID"
        )

    result = await db.execute(
        select(ScheduledQuery).where(ScheduledQuery.id == query_uuid)
    )
    query = result.scalar_one_or_none()

    if not query or query.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled query not found",
        )

    # Apply provided fields
    if body.query_text is not None:
        query.query_text = body.query_text
    if body.delivery is not None:
        query.delivery = body.delivery
    if body.delivery_email is not None:
        query.delivery_email = body.delivery_email
    if body.alert_condition is not None:
        query.alert_condition = body.alert_condition if body.alert_condition else None
    if body.alert_severity is not None:
        query.alert_severity = body.alert_severity
    if body.is_active is not None:
        query.is_active = body.is_active

    # Recompute next_run_at if cron changed or reactivating
    if body.cron_expression is not None:
        next_run = _compute_next_run(body.cron_expression)
        if next_run is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cron expression.",
            )
        query.cron_expression = body.cron_expression
        query.next_run_at = next_run
    elif body.is_active and not query.next_run_at:
        next_run = _compute_next_run(query.cron_expression)
        if next_run:
            query.next_run_at = next_run

    await db.commit()
    await db.refresh(query)

    return ScheduledQueryResponse(
        id=str(query.id),
        query_text=query.query_text,
        cron_expression=query.cron_expression,
        delivery=query.delivery,
        is_active=query.is_active,
        alert_condition=query.alert_condition,
        alert_severity=query.alert_severity,
        last_run_at=query.last_run_at.isoformat() if query.last_run_at else None,
        next_run_at=query.next_run_at.isoformat() if query.next_run_at else None,
        created_at=query.created_at.isoformat() if query.created_at else None,
    )



# ---------------------------------------------------------------------------
# DELETE /scheduled/{id} — delete a scheduled query
# ---------------------------------------------------------------------------
@router.delete("/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_query(
    query_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Permanently delete a scheduled query owned by the authenticated user."""
    try:
        query_uuid = uuid.UUID(query_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid query ID"
        )

    result = await db.execute(
        select(ScheduledQuery).where(ScheduledQuery.id == query_uuid)
    )
    query = result.scalar_one_or_none()

    if not query or query.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled query not found",
        )

    await db.delete(query)
    await db.commit()


# ---------------------------------------------------------------------------
# GET /scheduled/{id}/history — execution history
# ---------------------------------------------------------------------------
@router.get("/{query_id}/history", response_model=list[ScheduledReportResponse])
async def get_scheduled_history(
    query_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Return execution history for a specific scheduled query."""
    try:
        query_uuid = uuid.UUID(query_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid query ID"
        )

    # Verify ownership
    query_result = await db.execute(
        select(ScheduledQuery).where(ScheduledQuery.id == query_uuid)
    )
    query = query_result.scalar_one_or_none()

    if not query or query.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled query not found",
        )

    result = await db.execute(
        select(ScheduledReport)
        .where(ScheduledReport.scheduled_query_id == query_uuid)
        .order_by(ScheduledReport.executed_at.desc())
    )
    reports = result.scalars().all()

    return [
        ScheduledReportResponse(
            id=str(r.id),
            status=r.status,
            result_data=r.result_data,
            executed_at=r.executed_at.isoformat(),
        )
        for r in reports
    ]
