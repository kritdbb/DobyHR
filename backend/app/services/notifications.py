"""
Notification helpers – email & Google Chat webhooks.

Two webhook channels:
  • Town Crier  → GOOGLE_CHAT_WEBHOOK_URL      (badge awards, mana gifts, etc.)
  • Approvals   → GOOGLE_CHAT_APPROVAL_WEBHOOK (leave/expense/reward requests)

All run in background threads so endpoint latency is unaffected.
If URLs / credentials are not configured the helpers silently no-op.
"""

import logging
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.approval import ApprovalFlow, ApprovalStep, ApprovalStepApprover
from app.models.user import User

logger = logging.getLogger("hr-notifications")


# ── config checks ─────────────────────────────────────────

def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def _webhook_configured() -> bool:
    return bool(settings.GOOGLE_CHAT_WEBHOOK_URL)


def _approval_webhook_configured() -> bool:
    return bool(settings.GOOGLE_CHAT_APPROVAL_WEBHOOK)


# ── Approver lookup ───────────────────────────────────────

def find_step_approvers(
    user_id: int,
    step_order: int,
    db: Session,
) -> List[User]:
    """Return approver User objects for a given step_order in the user's approval flow."""
    flow = db.query(ApprovalFlow).filter(ApprovalFlow.target_user_id == user_id).first()
    if not flow:
        return []

    step = (
        db.query(ApprovalStep)
        .filter(ApprovalStep.flow_id == flow.id, ApprovalStep.step_order == step_order)
        .first()
    )
    if not step:
        return []

    approver_ids = [sa.approver_id for sa in step.approvers]
    if not approver_ids:
        return []

    return db.query(User).filter(User.id.in_(approver_ids)).all()


# ── Email ─────────────────────────────────────────────────

def _send_email_sync(to_emails: List[str], subject: str, html_body: str):
    """Blocking SMTP send – called from a background thread."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = ", ".join(to_emails)
        msg.attach(MIMEText(html_body, "html"))

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg["From"], to_emails, msg.as_string())
        server.quit()
        logger.info(f"📧 Email sent to {to_emails}")
    except Exception as e:
        logger.error(f"📧 Failed to send email: {e}")


def notify_approvers_by_email(
    requester_name: str,
    request_type: str,
    detail: str,
    approvers: List[User],
):
    """Fire-and-forget email to approver list."""
    if not _smtp_configured():
        return
    emails = [u.email for u in approvers if u.email]
    if not emails:
        return

    subject = f"🏰 DobyHR — New {request_type} awaiting your approval"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:24px;
                background:#1a1a2e;color:#e8d5b7;border:2px solid #d4a44c;border-radius:8px">
      <h2 style="color:#d4a44c;margin:0 0 12px">🏰 Approval Required</h2>
      <p><strong>{requester_name}</strong> submitted a <strong>{request_type}</strong>.</p>
      <p style="background:rgba(212,164,76,0.1);padding:12px;border-radius:6px;
                border:1px solid rgba(212,164,76,0.2)">{detail}</p>
      <p style="color:#8b7355;font-size:13px;margin-top:16px">
        Please log in to DobyHR to review and approve/reject.
      </p>
    </div>
    """
    threading.Thread(
        target=_send_email_sync,
        args=(emails, subject, html),
        daemon=True,
    ).start()


# ── Google Chat Webhook – Town Crier ──────────────────────

def _send_webhook_sync(url: str, text: str):
    """Blocking POST – called from a background thread."""
    try:
        r = httpx.post(url, json={"text": text}, timeout=10)
        logger.info(f"🔔 Webhook sent ({r.status_code})")
    except Exception as e:
        logger.error(f"🔔 Webhook failed: {e}")


def send_town_crier_webhook(text: str):
    """Fire-and-forget Google Chat message to Town Crier space."""
    if not _webhook_configured():
        return
    threading.Thread(
        target=_send_webhook_sync,
        args=(settings.GOOGLE_CHAT_WEBHOOK_URL, text),
        daemon=True,
    ).start()


# ── Google Chat Webhook – Approvals ───────────────────────

def send_approval_webhook(text: str):
    """Fire-and-forget Google Chat message to Approvals space."""
    if not _approval_webhook_configured():
        return
    threading.Thread(
        target=_send_webhook_sync,
        args=(settings.GOOGLE_CHAT_APPROVAL_WEBHOOK, text),
        daemon=True,
    ).start()


# ── Unified approver notification ─────────────────────────

def notify_approvers(
    requester_name: str,
    request_type: str,
    detail: str,
    approvers: List[User],
):
    """
    Notify approvers via all configured channels:
      1. Google Chat Webhook (approval space)
      2. Email (SMTP)
    """
    # Webhook to approval space
    approver_names = ", ".join(f"{u.name} {u.surname or ''}".strip() for u in approvers)
    text = f"🏰 *Approval Required*\n*{requester_name}* submitted a *{request_type}*.\n\n{detail}\n\nApprovers: {approver_names}"
    send_approval_webhook(text)

    # Email
    notify_approvers_by_email(requester_name, request_type, detail, approvers)
