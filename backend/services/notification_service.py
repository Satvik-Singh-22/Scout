"""
Banquoite — Notification Service

Sends email notifications for scheduled report deliveries using the Resend SDK.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Initialize Resend SDK
_resend_configured = False
try:
    import resend

    api_key = os.getenv("RESEND_API_KEY")
    if api_key and api_key != "re_your_key_here":
        resend.api_key = api_key
        _resend_configured = True
    else:
        logger.info("RESEND_API_KEY not configured — email delivery disabled")
except ImportError:
    logger.warning("resend package not installed — email delivery disabled")


def send_report_email(
    to_email: str,
    query_text: str,
    answer: str,
    executed_at: str,
) -> bool:
    """
    Send a scheduled report result via email.

    Args:
        to_email: Recipient email address
        query_text: The original scheduled query text
        answer: The AI-generated answer
        executed_at: ISO timestamp of when the report was generated

    Returns:
        True if the email was sent successfully, False otherwise
    """
    if not _resend_configured:
        logger.warning(
            "Email delivery skipped — Resend not configured. "
            "Would have sent report to %s",
            to_email,
        )
        return False

    try:
        resend.Emails.send(
            {
                "from": "reports@banquoite.app",
                "to": to_email,
                "subject": f"Banquoite Scheduled Report — {executed_at}",
                "html": f"""
                    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 24px; border-radius: 12px; margin-bottom: 20px;">
                            <h1 style="color: #e2e8f0; margin: 0; font-size: 20px;">📊 Banquoite Report</h1>
                        </div>
                        <div style="background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0;">
                            <h2 style="color: #1e293b; font-size: 16px; margin-top: 0;">Your Scheduled Report</h2>
                            <p style="color: #64748b; font-size: 14px;">
                                <strong>Query:</strong> {query_text}
                            </p>
                            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 16px 0;">
                            <div style="color: #334155; font-size: 14px; line-height: 1.6;">
                                {answer}
                            </div>
                        </div>
                        <p style="color: #94a3b8; font-size: 12px; text-align: center; margin-top: 20px;">
                            Delivered by Banquoite Intelligence Platform · {executed_at}
                        </p>
                    </div>
                """,
            }
        )
        logger.info("Report email sent to %s", to_email)
        return True

    except Exception as exc:
        logger.error("Failed to send report email to %s: %s", to_email, exc)
        return False


def send_alert_email(
    to_email: str,
    alert_title: str,
    alert_description: str,
    severity: str,
) -> bool:
    """
    Send an alert notification email.

    Args:
        to_email: Recipient email address
        alert_title: Alert title
        alert_description: Alert description
        severity: Alert severity (HIGH, MEDIUM, LOW)

    Returns:
        True if the email was sent successfully, False otherwise
    """
    if not _resend_configured:
        logger.warning("Alert email delivery skipped — Resend not configured")
        return False

    severity_colors = {
        "HIGH": "#ef4444",
        "MEDIUM": "#f59e0b",
        "LOW": "#3b82f6",
    }
    color = severity_colors.get(severity, "#6b7280")

    try:
        resend.Emails.send(
            {
                "from": "alerts@banquoite.app",
                "to": to_email,
                "subject": f"⚠️ Banquoite Alert [{severity}]: {alert_title}",
                "html": f"""
                    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: {color}; padding: 16px 24px; border-radius: 12px 12px 0 0;">
                            <h1 style="color: white; margin: 0; font-size: 18px;">⚠️ {severity} Alert</h1>
                        </div>
                        <div style="background: #f8fafc; padding: 20px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0; border-top: none;">
                            <h2 style="color: #1e293b; font-size: 16px; margin-top: 0;">{alert_title}</h2>
                            <p style="color: #334155; font-size: 14px; line-height: 1.6;">
                                {alert_description}
                            </p>
                        </div>
                        <p style="color: #94a3b8; font-size: 12px; text-align: center; margin-top: 20px;">
                            Banquoite Intelligence Platform — Anomaly Detection
                        </p>
                    </div>
                """,
            }
        )
        logger.info("Alert email sent to %s", to_email)
        return True

    except Exception as exc:
        logger.error("Failed to send alert email to %s: %s", to_email, exc)
        return False
