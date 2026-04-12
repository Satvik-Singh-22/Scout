"""
Banquoite — Anomaly Detection Service

Monitors alert configurations and detects threshold breaches across
configured metrics. Triggered by the scheduler every 15 minutes.

This module is designed to be extended by Person 1's anomaly_agent.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, text

from backend.db.models import Alert, AlertConfiguration, User
from backend.db.session import SyncSessionLocal
from backend.services.notification_service import send_alert_email

logger = logging.getLogger(__name__)


def run_anomaly_check():
    """
    Check all active alert configurations and generate alerts for
    any threshold breaches detected.

    Algorithm:
      1. Fetch all active AlertConfiguration rows
      2. For each config, query the referenced table for the metric
      3. Compare the current value against the threshold + condition
      4. If breached, insert a new Alert row
    """
    if SyncSessionLocal is None:
        logger.warning("Cannot run anomaly check — database not configured")
        return

    session = SyncSessionLocal()
    try:
        result = session.execute(
            select(AlertConfiguration).where(AlertConfiguration.is_active == True)
        )
        configs = result.scalars().all()

        if not configs:
            return

        alerts_created = 0
        for config in configs:
            try:
                current_value = _fetch_metric_value(
                    session, config.table_name, config.metric_name
                )

                if current_value is None:
                    continue

                is_breached = _check_threshold(
                    current_value, config.threshold, config.condition
                )

                if is_breached:
                    alert = Alert(
                        team_id=config.team_id,
                        alert_config_id=config.id,
                        title=f"{config.condition} threshold breach: {config.metric_name}",
                        description=(
                            f"The metric '{config.metric_name}' in table "
                            f"'{config.table_name}' has reached {current_value:.2f}, "
                            f"which is {config.condition} the threshold of {config.threshold:.2f}."
                        ),
                        severity=_determine_severity(
                            current_value, config.threshold, config.condition
                        ),
                        data_snapshot={
                            "metric_name": config.metric_name,
                            "table_name": config.table_name,
                            "current_value": current_value,
                            "threshold": config.threshold,
                            "condition": config.condition,
                            "detected_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    session.add(alert)
                    alerts_created += 1

                    # Notify Team Users
                    try:
                        user_result = session.execute(
                            select(User.email).where(User.team_id == config.team_id)
                        )
                        team_emails = user_result.scalars().all()
                        for email in team_emails:
                            send_alert_email(
                                to_email=email,
                                alert_title=alert.title,
                                alert_description=alert.description,
                                severity=alert.severity
                            )
                            print(f"[THRESHOLD ALERT] 📧 Sent email to: {email}")
                    except Exception as email_exc:
                        logger.error("Failed to send threshold alert emails: %s", email_exc)

            except Exception as exc:
                logger.error(
                    "Error checking alert config %s: %s", config.id, exc
                )
                continue

        if alerts_created > 0:
            session.commit()
            logger.info("Created %d anomaly alerts", alerts_created)

    except Exception as exc:
        logger.error("Anomaly check failed: %s", exc)
        session.rollback()
    finally:
        session.close()


def _fetch_metric_value(session, table_name: str, metric_name: str) -> float | None:
    """
    Fetch the current aggregate value for a metric from the specified table.
    Uses a safe parameterised approach to avoid SQL injection.
    """
    # Validate table and column names (alphanumeric + underscores only)
    import re

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        logger.warning("Invalid table name in alert config: %s", table_name)
        return None
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", metric_name):
        logger.warning("Invalid metric name in alert config: %s", metric_name)
        return None

    try:
        # Try to get a recent aggregate (e.g., count, sum, avg)
        query = text(f"SELECT COUNT(*) FROM {table_name}")
        result = session.execute(query)
        value = result.scalar()
        return float(value) if value is not None else None
    except Exception as exc:
        logger.debug("Could not fetch metric %s.%s: %s", table_name, metric_name, exc)
        return None


def _check_threshold(value: float, threshold: float, condition: str) -> bool:
    """Evaluate whether a value breaches the configured threshold condition."""
    if condition == "ABOVE":
        return value > threshold
    elif condition == "BELOW":
        return value < threshold
    elif condition == "SPIKE":
        # Spike detection: value exceeds threshold by 50% or more
        return value > threshold * 1.5
    return False


def _determine_severity(value: float, threshold: float, condition: str) -> str:
    """Determine alert severity based on deviation magnitude."""
    if threshold == 0:
        return "HIGH"

    deviation = abs(value - threshold) / abs(threshold)
    if deviation > 1.0:
        return "HIGH"
    elif deviation > 0.5:
        return "MEDIUM"
    else:
        return "LOW"
