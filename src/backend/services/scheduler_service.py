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

ELI5 (What does this file do?):
Think of this file as the heartbeat of our automated tasks.
While the rest of the application waits for users to click buttons, this file runs independently 
in the background on its own clock. Every 1 minute, it checks if any scheduled reports need to be sent out. 
Every 15 minutes, it checks if any data anomalies have occurred. It never sleeps!
"""

import asyncio
import logging
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

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# ---------------------------------------------------------------------------
# Phase 3 — Async Semaphore: limits concurrent Groq API calls to 2 at a time.
# Module-level so it is shared across all scheduler invocations in this process.
# ---------------------------------------------------------------------------
SCHEDULER_SEMAPHORE = asyncio.Semaphore(2)


def start_scheduler():
    """
    Register background jobs and start the scheduler.
    Called during FastAPI app startup via lifespan.
    """
    try:
        scheduler.add_job(
            run_due_scheduled_queries,
            "interval",
            minutes=1,
            id="scheduled_queries_runner",
            replace_existing=True,
            jitter=45,
        )
        scheduler.add_job(
            run_anomaly_detection,
            "interval",
            minutes=15,
            id="anomaly_detection_runner",
            replace_existing=True,
            jitter=45,
        )
        scheduler.start()
        logger.info("Background scheduler started with 2 jobs")
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

    Phase 3 architecture — Async Concurrent Execution:
      - All due queries are executed concurrently via asyncio.gather().
      - A module-level asyncio.Semaphore(2) limits simultaneous Groq API calls
        to 2 at any time, preventing RPM/TPM spike bursts.
      - Each pipeline.invoke() runs in a thread pool via asyncio.to_thread() so
        the synchronous LangGraph pipeline does not block the event loop.
      - return_exceptions=True ensures one failing query does not cancel others.

    Original sequential steps are preserved per-query (claim → pipeline → save).
    """
    if SyncSessionLocal is None:
        return

    session = SyncSessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Find due queries
        result = session.execute(
            select(ScheduledQuery).where(
                ScheduledQuery.is_active == True,
                ScheduledQuery.next_run_at <= now,
            )
        )
        due_queries = result.scalars().all()

        if not due_queries:
            return

        logger.info("Found %d due scheduled queries", len(due_queries))

        # ── STEP 1: CLAIM all due queries by advancing next_run_at ──
        # This prevents the next scheduler tick from picking them up again
        for sq in due_queries:
            try:
                parts = sq.cron_expression.strip().split()
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                )
                sq.next_run_at = trigger.get_next_fire_time(None, now)
            except Exception:
                sq.next_run_at = None
                sq.is_active = False
        session.commit()
        logger.info("Claimed %d queries — next_run_at advanced", len(due_queries))

        # ── STEP 2: Batch-fetch users and access for all due queries (avoids N+1) ──
        due_user_ids = list({sq.user_id for sq in due_queries if sq.is_active})
        users_result = session.execute(
            select(User).where(User.id.in_(due_user_ids))
        )
        users_by_id = {u.id: u for u in users_result.scalars().all()}

        access_result = session.execute(
            select(UserTeamAccess.user_id, UserTeamAccess.team_id)
            .where(UserTeamAccess.user_id.in_(due_user_ids))
        )
        from collections import defaultdict
        access_by_user: dict[object, list[str]] = defaultdict(list)
        for row in access_result.all():
            access_by_user[row.user_id].append(str(row.team_id))

        # ── STEP 3: Define the async worker for a single scheduled query ──
        async def process_single_query(sq: ScheduledQuery) -> None:
            """
            Inner worker executed concurrently for each due query.

            The asyncio.Semaphore wraps ONLY the pipeline.invoke() call
            (the actual Groq API round-trip) so pre/post-processing steps
            such as DB reads, email delivery, and alert creation run freely
            without consuming quota.
            """
            if not sq.is_active:
                return

            print(f"\n[SCHEDULER] 🔔 Picking up scheduled query: '{sq.query_text[:100]}...' (ID: {sq.id})")

            # Look up user from batch cache
            user = users_by_id.get(sq.user_id)
            if not user:
                logger.warning("No user found for scheduled query %s (user_id=%s)", sq.id, sq.user_id)
                return

            # Look up access from batch cache
            access_team_ids = access_by_user.get(user.id, [])

            state = {
                "user_query": sq.query_text,
                "user_id": str(user.id),
                "user_persona": user.persona,
                "team_id": str(user.team_id) if user.team_id else "",
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

            # ── Semaphore-controlled pipeline invocation ──
            # The semaphore limits to 2 simultaneous Groq API calls.
            # asyncio.to_thread offloads the synchronous pipeline to a thread
            # so the event loop is never blocked.
            try:
                from backend.agents.pipeline import pipeline

                async with SCHEDULER_SEMAPHORE:
                    result_state = await asyncio.to_thread(pipeline.invoke, state)

                answer = result_state.get("final_answer", "Pipeline returned no answer")
                report_status = "SUCCESS"
            except Exception as pipeline_exc:
                logger.error("Pipeline error for scheduled query %s: %s", sq.id, pipeline_exc)
                answer = f"Pipeline error: {str(pipeline_exc)}"
                report_status = "FAILED"
                result_state = {}

            # All post-processing (DB writes, email, alerts) runs outside the semaphore
            try:
                # Save report
                report = ScheduledReport(
                    scheduled_query_id=sq.id,
                    result_data={"answer": answer, "query_text": sq.query_text},
                    status=report_status,
                )
                session.add(report)

                # Handle delivery
                if report_status == "SUCCESS":
                    if sq.delivery == "DASHBOARD":
                        card = DashboardCard(
                            user_id=sq.user_id,
                            title=f"Scheduled: {sq.query_text[:100]}",
                            query_result={"answer": answer},
                            chart_type="TABLE",
                        )
                        session.add(card)
                        print(f"[SCHEDULER] 📊 Uploaded result to Dashboard for User: {user.email}")

                    elif sq.delivery == "EMAIL" and sq.delivery_email:
                        try:
                            from backend.services.notification_service import send_report_email

                            send_report_email(
                                to_email=sq.delivery_email,
                                query_text=sq.query_text,
                                answer=answer,
                                executed_at=now.isoformat(),
                            )
                            print(f"[SCHEDULER] 📧 Sent report email to: {sq.delivery_email}")
                        except Exception as email_exc:
                            logger.error("Email delivery failed for query %s: %s", sq.id, email_exc)

                # Evaluate alert condition if configured
                if report_status == "SUCCESS" and sq.alert_condition:
                    logger.info(
                        "Evaluating alert condition for query %s: '%s'",
                        sq.id, sq.alert_condition[:80]
                    )
                    try:
                        triggered, reason = _evaluate_alert_condition(
                            answer, sq.alert_condition
                        )
                        logger.info(
                            "Alert evaluation result for %s: triggered=%s, reason=%s",
                            sq.id, triggered, reason[:100]
                        )
                        if triggered:
                            alert_severity = sq.alert_severity or "MEDIUM"
                            alert = Alert(
                                team_id=user.team_id,
                                title=f"Scheduled alert: {sq.query_text[:80]}",
                                description=reason,
                                severity=alert_severity,
                                data_snapshot={
                                    "query_text": sq.query_text,
                                    "alert_condition": sq.alert_condition,
                                    "answer_excerpt": answer[:500],
                                    "detected_at": now.isoformat(),
                                },
                            )
                            session.add(alert)
                            logger.info(
                                "Alert CREATED for scheduled query %s (severity=%s)",
                                sq.id, alert_severity
                            )
                            # Send Alert Email
                            alert_recipient = sq.delivery_email or user.email
                            if alert_recipient:
                                send_alert_email(
                                    to_email=alert_recipient,
                                    alert_title=f"Scheduled alert: {sq.query_text[:80]}",
                                    alert_description=reason,
                                    severity=alert_severity
                                )
                                print(f"[SCHEDULER] ⚠️ Sent Legacy Alert email to: {alert_recipient}")
                        else:
                            logger.info(
                                "Alert NOT triggered for query %s: %s",
                                sq.id, reason[:100]
                            )
                    except Exception as alert_exc:
                        logger.error(
                            "Alert evaluation failed for query %s: %s",
                            sq.id, alert_exc,
                            exc_info=True
                        )

                # --- INLINE ANOMALY CHECK ---
                if report_status == "SUCCESS":
                    sql_results = result_state.get("sql_results", [])
                    relevant_tables = result_state.get("relevant_tables", [])

                    if sql_results and relevant_tables:
                        logger.info("Triggering inline anomaly check for query %s", sq.id)

                        # Step 1: Reasoner — what anomalies COULD exist?
                        reasoner_output = anomaly_reasoner_agent(
                            user_query=sq.query_text,
                            relevant_tables=relevant_tables,
                            sql_results=sql_results,
                            team_id=str(user.team_id),
                            current_date=now.date().isoformat(),
                        )

                        # Step 2: Checker — do they actually exist?
                        if reasoner_output:
                            confirmed_alerts = anomaly_checker_agent(
                                reasoner_output=reasoner_output,
                                team_id=str(user.team_id),
                            )

                            for alert_data in confirmed_alerts:
                                alert = Alert(
                                    team_id=user.team_id,
                                    title=alert_data["title"],
                                    description=alert_data["description"],
                                    severity=alert_data["severity"],
                                    data_snapshot=alert_data["data_snapshot"],
                                    is_read=False,
                                    created_at=datetime.now(timezone.utc)
                                )
                                session.add(alert)
                                logger.info("Inline anomaly ALERT created: %s", alert_data["title"])

                                # Send Anomaly Email
                                if user.email:
                                    send_alert_email(
                                        to_email=user.email,
                                        alert_title=alert_data["title"],
                                        alert_description=alert_data["description"],
                                        severity=alert_data["severity"]
                                    )
                                    print(f"[SCHEDULER] ⚠️ Sent Inline Anomaly email to: {user.email}")

                # Update last_run_at
                sq.last_run_at = now
                session.commit()
                logger.info("Executed scheduled query %s — status: %s", sq.id, report_status)

            except Exception as exc:
                logger.error("Error in post-processing for scheduled query %s: %s", sq.id, exc, exc_info=True)
                try:
                    session.rollback()
                except Exception:
                    pass

        # ── STEP 4: Execute all workers concurrently ──
        # return_exceptions=True ensures one failure does not cancel other tasks.
        tasks = [process_single_query(sq) for sq in due_queries]
        await asyncio.gather(*tasks, return_exceptions=True)

    except Exception as exc:
        logger.error("Scheduled queries runner error: %s", exc, exc_info=True)
    finally:
        session.close()


async def run_anomaly_detection():
    """
    Run anomaly detection across configured alert thresholds.

    1. Import run_anomaly_check from anomaly_service
    2. Call it with a DB session
    3. For each triggered alert: insert into alerts table
    """
    try:
        from backend.services.anomaly_service import run_anomaly_check

        run_anomaly_check()
    except Exception as exc:
        logger.warning("Anomaly detection run failed (non-fatal): %s", exc)


def _evaluate_alert_condition(
    query_result: str, alert_condition: str
) -> tuple[bool, str]:
    """
    Use the LLM to evaluate whether an English-text alert condition is met
    given a query result.

    Returns:
        (triggered: bool, reason: str)
    """
    import json

    content = ""  # Initialize so it's always defined for error handling

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


