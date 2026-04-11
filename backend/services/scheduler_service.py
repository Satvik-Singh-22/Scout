"""
Banquoite — Scheduler Service

Manages APScheduler background jobs:
  1. run_due_scheduled_queries() — every 1 minute
  2. run_anomaly_detection()     — every 15 minutes

Started/stopped via the FastAPI lifespan context manager in main.py.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from backend.db.models import (
    DashboardCard,
    ScheduledQuery,
    ScheduledReport,
    User,
)
from backend.db.session import SyncSessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


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
        )
        scheduler.add_job(
            run_anomaly_detection,
            "interval",
            minutes=15,
            id="anomaly_detection_runner",
            replace_existing=True,
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

    For each due query:
      1. Build PipelineState with query_text as user_query
      2. Run pipeline.invoke() synchronously
      3. Save result to scheduled_reports table
      4. If delivery == 'DASHBOARD': create dashboard_card record
      5. If delivery == 'EMAIL': call notification_service.send_report_email()
      6. Update last_run_at and next_run_at on the scheduled_query
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

        for sq in due_queries:
            try:
                # Fetch the user for this query
                user_result = session.execute(
                    select(User).where(User.id == sq.user_id)
                )
                user = user_result.scalar_one_or_none()
                if not user:
                    continue

                # Try to invoke the pipeline
                try:
                    from backend.agents.pipeline import pipeline

                    state = {
                        "user_query": sq.query_text,
                        "user_id": str(user.id),
                        "user_persona": user.persona,
                        "team_id": str(user.team_id) if user.team_id else "",
                        "allowed_team_ids": [str(user.team_id)] if user.team_id else [],
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
                    result_state = pipeline.invoke(state)
                    answer = result_state.get("final_answer", "Pipeline returned no answer")
                    report_status = "SUCCESS"
                except Exception as pipeline_exc:
                    logger.error("Pipeline error for scheduled query %s: %s", sq.id, pipeline_exc)
                    answer = f"Pipeline error: {str(pipeline_exc)}"
                    report_status = "FAILED"

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

                    elif sq.delivery == "EMAIL" and sq.delivery_email:
                        try:
                            from backend.services.notification_service import send_report_email

                            send_report_email(
                                to_email=sq.delivery_email,
                                query_text=sq.query_text,
                                answer=answer,
                                executed_at=now.isoformat(),
                            )
                        except Exception as email_exc:
                            logger.error("Email delivery failed for query %s: %s", sq.id, email_exc)

                # Update run timestamps
                sq.last_run_at = now

                # Compute next run
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
                    sq.is_active = False  # Disable if cron is invalid

                session.commit()
                logger.info("Executed scheduled query %s — status: %s", sq.id, report_status)

            except Exception as exc:
                logger.error("Error processing scheduled query %s: %s", sq.id, exc)
                session.rollback()

    except Exception as exc:
        logger.error("Scheduled queries runner error: %s", exc)
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
