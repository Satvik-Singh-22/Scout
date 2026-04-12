"""
Banquoite — Notification Service

ELI5 (What does this file do?):
Think of this file as the company postman. 
Whenever someone needs to receive an email—whether it's a regular weekly report or an urgent 
warning that the database is failing—our system gives the message to this file. 
It formats the email to look pretty and professional, slaps a stamp on it, and sends it out to the user's inbox securely.
"""

import logging
import os
import requests
import html

logger = logging.getLogger(__name__)

# MailerSend Configuration
MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")
# MAILERSEND_URL = "https://api.api-client.com/v1/email" # Typical pattern, but let's use the one from the user
MAILERSEND_URL = "https://api.mailersend.com/v1/email"
FROM_EMAIL = "noreply@test-nrw7gym0w3kg2k8e.mlsender.net"
FROM_NAME = "Scout"

def _send_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
    """Helper to send email via MailerSend API."""
    if not MAILERSEND_API_KEY:
        logger.warning("MAILERSEND_API_KEY not configured — email delivery disabled")
        return False

    headers = {
        "Authorization": f"Bearer {MAILERSEND_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "from": {
            "email": FROM_EMAIL,
            "name": FROM_NAME
        },
        "to": [
            {
                "email": to_email,
                "name": "User"
            }
        ],
        "subject": subject,
        "html": html_content,
        "text": text_content or "Please use an HTML capable email client to view this message."
    }

    try:
        response = requests.post(MAILERSEND_URL, headers=headers, json=data, timeout=10)
        if response.status_code in [200, 202]:
            logger.info("Email sent successfully to %s (Status: %s)", to_email, response.status_code)
            return True
        else:
            logger.error("MailerSend failed: %s - %s", response.status_code, response.text)
            return False
    except Exception as e:
        logger.error("Error sending email via MailerSend: %s", e)
        return False

def send_report_email(
    to_email: str,
    query_text: str,
    answer: str,
    executed_at: str,
) -> bool:
    """Send a scheduled report result via email."""
    subject = f"Scout Scheduled Report — {executed_at}"
    
    # Escape user content
    safe_query = html.escape(query_text)
    safe_answer = html.escape(answer)
    
    html_content = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 24px; border-radius: 12px; margin-bottom: 20px;">
                <h1 style="color: #e2e8f0; margin: 0; font-size: 20px;">📊 Scout Report</h1>
            </div>
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0;">
                <h2 style="color: #1e293b; font-size: 16px; margin-top: 0;">Your Scheduled Report</h2>
                <p style="color: #64748b; font-size: 14px;">
                    <strong>Query:</strong> {safe_query}
                </p>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 16px 0;">
                <div style="color: #334155; font-size: 14px; line-height: 1.6;">
                    {safe_answer}
                </div>
            </div>
            <p style="color: #94a3b8; font-size: 12px; text-align: center; margin-top: 20px;">
                Delivered by Scout Intelligence Platform · {executed_at}
            </p>
        </div>
    """
    return _send_email(to_email, subject, html_content, text_content=f"Report for: {query_text}")

def send_alert_email(
    to_email: str,
    alert_title: str,
    alert_description: str,
    severity: str,
) -> bool:
    """Send an alert notification email."""
    severity_colors = {
        "HIGH": "#ef4444",
        "MEDIUM": "#f59e0b",
        "LOW": "#3b82f6",
    }
    color = severity_colors.get(severity, "#6b7280")
    subject = f"⚠️ Scout Alert [{severity}]: {alert_title}"

    # Escape user content
    safe_title = html.escape(alert_title)
    safe_description = html.escape(alert_description)

    html_content = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: {color}; padding: 16px 24px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 18px;">⚠️ {severity} Alert</h1>
            </div>
            <div style="background: #f8fafc; padding: 20px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0; border-top: none;">
                <h2 style="color: #1e293b; font-size: 16px; margin-top: 0;">{safe_title}</h2>
                <p style="color: #334155; font-size: 14px; line-height: 1.6;">
                    {safe_description}
                </p>
            </div>
            <p style="color: #94a3b8; font-size: 12px; text-align: center; margin-top: 20px;">
                Scout Intelligence Platform — Anomaly Detection
            </p>
        </div>
    """
    return _send_email(to_email, subject, html_content, text_content=f"Alert: {alert_title}")
