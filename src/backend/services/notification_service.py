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
import smtplib
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# SMTP Configuration (Gmail)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")          # your Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")   # Gmail App Password (16-char)
FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER or "")
FROM_NAME = os.getenv("SMTP_FROM_NAME", "Scout")

def _send_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
    """Helper to send email via SMTP (Gmail)."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP_USER / SMTP_PASSWORD not configured — email delivery disabled")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach plain-text fallback and HTML body
    msg.attach(MIMEText(text_content or "Please use an HTML capable email client to view this message.", "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        logger.info("Email sent successfully to %s via SMTP", to_email)
        return True
    except Exception as e:
        logger.error("Error sending email via SMTP: %s", e)
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
