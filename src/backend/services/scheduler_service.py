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
Banquoite — Scheduler Service

ELI5 (What does this file do?):\nThink of this file as the heartbeat of our automated tasks.
While the rest of the application waits for users to click buttons, this file runs independently
in the background on its own clock. Every 1 minute, it checks if any scheduled reports need to be sent out.
Every 15 minutes, it checks if any data anomalies have occurred. It never sleeps!

Architecture notes (Phase 3):
  - AsyncIOScheduler runs on the same event loop as FastAPI — zero extra threads needed.
  - A shared asyncio.Semaphore(2) caps concurrent Groq API calls to prevent rate-limit bursts.
  - All blocking work (pipeline.invoke, LLM calls, agent calls) is offloaded via
    asyncio.to_thread() so the event loop (and therefore the website) is never blocked.
  - Each concurrent worker owns its own SQLAlchemy Session — sessions are NOT thread-safe
    and must never be shared across concurrent tasks.
  - A "snapshot" pattern is used: all ORM objects are converted to plain dicts before
    asyncio.gather() runs, preventing detached-instance errors.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from backend.db.models import (
    Alert,
    DashboardCard,
    ScheduledQuery,
    ScheduledReport,
    User,
    UserTeamAccess,
)
from backend.db.session import SyncSessionLocal
from backend.agents.anomaly_reasoner_agent import anomaly_reasoner_agent
from backend.agents.anomaly_checker_agent import anomaly_checker_agent
from backend.services.notification_service import send_report_email, send_alert_email
from backend.services.sync_workflow_data import sync_workflow_data

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# ---------------------------------------------------------------------------
# Semaphore: limits concurrent Groq API calls to 2 at a time.
# Module-level so it is shared across all scheduler invocations in this process.
# ---------------------------------------------------------------------------
SCHEDULER_SEMAPHORE = asyncio.Semaphore(2)


def start_scheduler():
    """
    Register background jobs and start the scheduler.
    Called during FastAPI app startup via lifespan.

    NOTE: No jitter — jitter on a 1-minute interval causes jobs to fire at random
    times within ±45 s of the tick, which causes scheduled tasks to be missed or
    double-executed. Predictable intervals are essential for cron correctness.
    """
    try:
        scheduler.add_job(
            run_due_scheduled_queries,
            "interval",
            minutes=1,
            id="scheduled_queries_runner",
            replace_existing=True,
        )
        scheduler.add_job(
            run_anomaly_detection,
            "interval",
            minutes=15,
            id="anomaly_detection_runner",
            replace_existing=True,
        )
        scheduler.add_job(
            sync_workflow_data,
            "interval",
            hours=6,
            id="sync_workflow_data_runner",
            next_run_time=datetime.now(timezone.utc),  # Start immediately and run every 6h
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Background scheduler started with 3 jobs (1 paused)")
    except Exception as exc:
        logger.warning("Scheduler startup failed (non-fatal): %s", exc)


def shutdown_scheduler():
    """
    Gracefully stop the scheduler.
    Called during FastAPI app shutdown via lifespan.
    """
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Background scheduler stopped")
    except Exception as exc:
        logger.warning("Scheduler shutdown error (non-fatal): %s", exc)


async def run_due_scheduled_queries():
    """
    Check for scheduled queries whose next_run_at <= now and execute them.

    Execution flow:
      STEP 1 — CLAIM:  Short-lived session finds due queries, advances next_run_at,
                        and snapshots all fields to plain dicts. Session closed.
      STEP 2 — LOOKUP: Short-lived session batch-fetches users/access, snapshots
                        to plain dicts. Session closed.
      STEP 3 — WORK:   Each query runs in its own async worker with its own session.
                        asyncio.gather() runs all workers concurrently.
                        Semaphore(2) caps simultaneous Groq API calls.
                        All blocking calls use asyncio.to_thread().
    """
    if SyncSessionLocal is None:
        return

    now = datetime.now(timezone.utc)

    # ── STEP 1: CLAIM — find due queries, advance next_run_at, snapshot ──────
    due_query_snapshots: list[dict] = []

    claim_session = SyncSessionLocal()
    try:
        result = claim_session.execute(
            select(ScheduledQuery).where(
                ScheduledQuery.is_active == True,  # noqa: E712
                ScheduledQuery.next_run_at <= now,
            )
        )
        due_queries = result.scalars().all()

        if not due_queries:
            return

        logger.info("Found %d due scheduled queries", len(due_queries))

        for sq in due_queries:
            # Advance next_run_at so the next tick won't re-claim this query
            try:
                parts = sq.cron_expression.strip().split()
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                    timezone="UTC",  # Always UTC — never local system time
                )
                next_fire = trigger.get_next_fire_time(None, now)
                # Guard: ensure result is always timezone-aware
                if next_fire is not None and next_fire.tzinfo is None:
                    next_fire = next_fire.replace(tzinfo=timezone.utc)
                sq.next_run_at = next_fire
            except Exception:
                sq.next_run_at = None
                sq.is_active = False

            # Snapshot to plain dict — workers must not use ORM objects from
            # a closed session (detached-instance error).
            due_query_snapshots.append({
                "id": sq.id,
                "user_id": sq.user_id,
                "query_text": sq.query_text,
                "cron_expression": sq.cron_expression,
                "delivery": sq.delivery,
                "delivery_email": sq.delivery_email,
                "alert_condition": sq.alert_condition,
                "alert_severity": sq.alert_severity,
                "is_active": sq.is_active,
            })

        claim_session.commit()
        logger.info("Claimed %d queries — next_run_at advanced", len(due_query_snapshots))

    except Exception as exc:
        logger.error("Scheduled queries claim step failed: %s", exc, exc_info=True)
        try:
            claim_session.rollback()
        except Exception:
            pass
        return
    finally:
        claim_session.close()

    # ── STEP 2: LOOKUP — batch-fetch users & access, snapshot to plain dicts ─
    due_user_ids = list({snap["user_id"] for snap in due_query_snapshots if snap["is_active"]})
    users_by_id: dict = {}
    access_by_user: dict = {}

    if due_user_ids:
        lookup_session = SyncSessionLocal()
        try:
            users_result = lookup_session.execute(
                select(User).where(User.id.in_(due_user_ids))
            )
            for u in users_result.scalars().all():
                users_by_id[u.id] = {
                    "id": u.id,
                    "email": u.email,
                    "persona": u.persona,
                    "team_id": u.team_id,
                }

            access_result = lookup_session.execute(
                select(UserTeamAccess.user_id, UserTeamAccess.team_id)
                .where(UserTeamAccess.user_id.in_(due_user_ids))
            )
            ab: dict = defaultdict(list)
            for row in access_result.all():
                ab[row.user_id].append(str(row.team_id))
            access_by_user = dict(ab)
        except Exception as exc:
            logger.error("Scheduler user-lookup step failed: %s", exc, exc_info=True)
        finally:
            lookup_session.close()

    # ── STEP 3: WORK — concurrent per-query workers ───────────────────────────
    async def process_single_query(snap: dict) -> None:
        """
        Async worker for one scheduled query.

        Thread/session safety rules upheld:
          - Uses only plain-dict snapshots (no detached ORM objects).
          - Creates and owns its own SyncSessionLocal() — never shares sessions.
          - All blocking I/O (pipeline, LLM, agents) goes through asyncio.to_thread().
        """
        if not snap["is_active"]:
            return

        sq_id = snap["id"]
        print(f"\n[SCHEDULER] 🔔 Running scheduled query: '{snap['query_text'][:80]}...' (ID: {sq_id})")

        user = users_by_id.get(snap["user_id"])
        if not user:
            logger.warning("No user found for scheduled query %s (user_id=%s)", sq_id, snap["user_id"])
            return

        access_team_ids = access_by_user.get(user["id"], [])

        state = {
            "user_query": snap["query_text"],
            "user_id": str(user["id"]),
            "user_persona": user["persona"],
            "team_id": str(user["team_id"]) if user["team_id"] else "",
            "allowed_team_ids": access_team_ids,
            "current_date": now.date().isoformat(),
            "query_intent": "",
            "routing_decision": {},
            "relevant_tables": [],
            "generated_sql": "",
            "sql_results": [],
            "rag_chunks": [],
            "synthesized_context": "",
            "final_answer": "",
            "chain_of_thought": {},
        }

        # ── Pipeline invocation (blocking — offloaded to thread pool) ──────────
        # The semaphore limits to 2 simultaneous Groq API calls.
        try:
            from backend.agents.pipeline import pipeline

            async with SCHEDULER_SEMAPHORE:
                result_state = await asyncio.to_thread(pipeline.invoke, state)

            answer = result_state.get("final_answer", "Pipeline returned no answer")
            report_status = "SUCCESS"
        except Exception as pipeline_exc:
            logger.error("Pipeline error for scheduled query %s: %s", sq_id, pipeline_exc)
            answer = f"Pipeline error: {str(pipeline_exc)}"
            report_status = "FAILED"
            result_state = {}

        # ── All DB writes use this worker's own isolated session ───────────────
        worker_session = SyncSessionLocal()
        try:
            # 1. Save execution report
            worker_session.add(ScheduledReport(
                scheduled_query_id=sq_id,
                result_data={"answer": answer, "query_text": snap["query_text"]},
                status=report_status,
            ))

            # 2. Delivery
            if report_status == "SUCCESS":
                if snap["delivery"] == "DASHBOARD":
                    worker_session.add(DashboardCard(
                        user_id=snap["user_id"],
                        title=f"Scheduled: {snap['query_text'][:100]}",
                        query_result={"answer": answer},
                        chart_type="TABLE",
                    ))
                    print(f"[SCHEDULER] 📊 Dashboard card created for: {user['email']}")

                elif snap["delivery"] == "EMAIL" and snap["delivery_email"]:
                    try:
                        send_report_email(
                            to_email=snap["delivery_email"],
                            query_text=snap["query_text"],
                            answer=answer,
                            executed_at=now.isoformat(),
                        )
                        print(f"[SCHEDULER] 📧 Report email sent to: {snap['delivery_email']}")
                    except Exception as email_exc:
                        logger.error("Email delivery failed for query %s: %s", sq_id, email_exc)

            # 3. Alert condition evaluation (blocking LLM call — offloaded to thread)
            if report_status == "SUCCESS" and snap["alert_condition"]:
                logger.info("Evaluating alert condition for query %s", sq_id)
                try:
                    triggered, reason = await asyncio.to_thread(
                        _evaluate_alert_condition, answer, snap["alert_condition"]
                    )
                    logger.info(
                        "Alert evaluation for %s: triggered=%s reason=%s",
                        sq_id, triggered, reason[:100]
                    )
                    if triggered:
                        alert_severity = snap["alert_severity"] or "MEDIUM"
                        worker_session.add(Alert(
                            team_id=user["team_id"],
                            title=f"Scheduled alert: {snap['query_text'][:80]}",
                            description=reason,
                            severity=alert_severity,
                            data_snapshot={
                                "query_text": snap["query_text"],
                                "alert_condition": snap["alert_condition"],
                                "answer_excerpt": answer[:500],
                                "detected_at": now.isoformat(),
                            },
                        ))
                        logger.info("Alert created for query %s (severity=%s)", sq_id, alert_severity)
                        alert_recipient = snap["delivery_email"] or user["email"]
                        if alert_recipient:
                            send_alert_email(
                                to_email=alert_recipient,
                                alert_title=f"Scheduled alert: {snap['query_text'][:80]}",
                                alert_description=reason,
                                severity=alert_severity,
                            )
                            print(f"[SCHEDULER] ⚠️ Alert email sent to: {alert_recipient}")
                    else:
                        logger.info("Alert NOT triggered for query %s: %s", sq_id, reason[:100])
                except Exception as alert_exc:
                    logger.error("Alert evaluation failed for query %s: %s", sq_id, alert_exc, exc_info=True)

            # 4. Inline anomaly check (blocking agents — offloaded to thread)
            if report_status == "SUCCESS":
                sql_results = result_state.get("sql_results", [])
                relevant_tables = result_state.get("relevant_tables", [])

                if sql_results and relevant_tables:
                    logger.info("Triggering inline anomaly check for query %s", sq_id)
                    try:
                        reasoner_output = await asyncio.to_thread(
                            anomaly_reasoner_agent,
                            user_query=snap["query_text"],
                            relevant_tables=relevant_tables,
                            sql_results=sql_results,
                            team_id=str(user["team_id"]),
                            current_date=now.date().isoformat(),
                        )

                        if reasoner_output:
                            confirmed_alerts = await asyncio.to_thread(
                                anomaly_checker_agent,
                                reasoner_output=reasoner_output,
                                team_id=str(user["team_id"]),
                            )

                            for alert_data in confirmed_alerts:
                                worker_session.add(Alert(
                                    team_id=user["team_id"],
                                    title=alert_data["title"],
                                    description=alert_data["description"],
                                    severity=alert_data["severity"],
                                    data_snapshot=alert_data["data_snapshot"],
                                    is_read=False,
                                    created_at=datetime.now(timezone.utc),
                                ))
                                logger.info("Inline anomaly alert created: %s", alert_data["title"])
                                if user["email"]:
                                    send_alert_email(
                                        to_email=user["email"],
                                        alert_title=alert_data["title"],
                                        alert_description=alert_data["description"],
                                        severity=alert_data["severity"],
                                    )
                                    print(f"[SCHEDULER] ⚠️ Anomaly email sent to: {user['email']}")
                    except Exception as anomaly_exc:
                        logger.error("Anomaly check failed for query %s: %s", sq_id, anomaly_exc, exc_info=True)

            # 5. Update last_run_at (re-fetch from this worker's session)
            sq_row = worker_session.execute(
                select(ScheduledQuery).where(ScheduledQuery.id == sq_id)
            ).scalar_one_or_none()
            if sq_row:
                sq_row.last_run_at = now

            worker_session.commit()
            logger.info("Scheduled query %s completed — status: %s", sq_id, report_status)

        except Exception as exc:
            logger.error(
                "Post-processing failed for scheduled query %s: %s", sq_id, exc, exc_info=True
            )
            try:
                worker_session.rollback()
            except Exception:
                pass
        finally:
            worker_session.close()

    # Run all workers concurrently; return_exceptions=True so one failure
    # never cancels the other queries.
    await asyncio.gather(
        *[process_single_query(snap) for snap in due_query_snapshots],
        return_exceptions=True,
    )


async def run_anomaly_detection():
    """
    Run anomaly detection across configured alert thresholds every 15 minutes.
    Wraps the synchronous anomaly_service in asyncio.to_thread() so the
    event loop is never blocked.
    """
    try:
        from backend.services.anomaly_service import run_anomaly_check

        await asyncio.to_thread(run_anomaly_check)
    except Exception as exc:
        logger.warning("Anomaly detection run failed (non-fatal): %s", exc)


def _evaluate_alert_condition(
    query_result: str, alert_condition: str
) -> tuple[bool, str]:
    """
    Use the LLM to evaluate whether an English-text alert condition is met
    given a query result.

    NOTE: This function is synchronous by design — it must be called via
    asyncio.to_thread() from async code to avoid blocking the event loop.

    Returns:
        (triggered: bool, reason: str)
    """
    import json

    content = ""  # Always defined for safe error handling

    try:
        from backend.agents.llm import get_llm

        llm = get_llm(temperature=0, json_mode=True)

        prompt = (
            "You are a data alert evaluator. Given a query result and an alert condition, "
            "determine if the condition is met.\n\n"
            f"QUERY RESULT:\n{query_result[:2000]}\n\n"
            f"ALERT CONDITION:\n{alert_condition}\n\n"
            "Respond with ONLY this JSON format (no extra text):\n"
            '{"triggered": true, "reason": "the value 9999.75 exceeds the threshold of 5"}\n'
            "or\n"
            '{"triggered": false, "reason": "the value is within acceptable range"}\n'
        )

        logger.info("Calling LLM for alert evaluation...")
        response = llm.invoke(prompt)
        content = response.content.strip()
        logger.info("LLM alert response: %s", content[:300])

        parsed = json.loads(content)
        triggered = bool(parsed.get("triggered", False))
        reason = str(parsed.get("reason", "Alert condition evaluated"))

        return triggered, reason

    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON for alert evaluation: %s", content[:300])
        return False, "Could not parse LLM response"
    except Exception as exc:
        logger.error("Alert condition evaluation error: %s", exc, exc_info=True)
        return False, f"Evaluation error: {str(exc)}"
