"""
Notification helpers – email, Google Chat webhook & Google Chat DM.

All run in background threads so endpoint latency is unaffected.
If credentials / URLs are not configured the helpers silently no-op.
"""

import json
import logging
import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

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


def _chat_dm_configured() -> bool:
    path = settings.GOOGLE_CHAT_SA_KEY_FILE
    return bool(path and os.path.isfile(path))


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


# ── Google Chat Webhook ───────────────────────────────────

def _send_webhook_sync(text: str):
    """Blocking POST – called from a background thread."""
    try:
        r = httpx.post(
            settings.GOOGLE_CHAT_WEBHOOK_URL,
            json={"text": text},
            timeout=10,
        )
        logger.info(f"🔔 Webhook sent ({r.status_code})")
    except Exception as e:
        logger.error(f"🔔 Webhook failed: {e}")


def send_town_crier_webhook(text: str):
    """Fire-and-forget Google Chat message."""
    if not _webhook_configured():
        return
    threading.Thread(
        target=_send_webhook_sync,
        args=(text,),
        daemon=True,
    ).start()


# ── Google Chat DM (Service Account) ─────────────────────

_CHAT_API = "https://chat.googleapis.com/v1"
_CHAT_SCOPE = "https://www.googleapis.com/auth/chat.bot"


def _get_chat_access_token() -> Optional[str]:
    """Get an access token from the service account key file."""
    try:
        from google.oauth2 import service_account as sa
        creds = sa.Credentials.from_service_account_file(
            settings.GOOGLE_CHAT_SA_KEY_FILE,
            scopes=[_CHAT_SCOPE],
        )
        creds.refresh(httpx_request_adapter())
        return creds.token
    except Exception as e:
        logger.error(f"💬 Chat DM — failed to get access token: {e}")
        return None


class httpx_request_adapter:
    """Minimal adapter so google-auth can use httpx instead of requests."""

    def __call__(self, request):
        resp = httpx.request(
            method=request.method,
            url=request.url,
            headers=dict(request.headers),
            content=request.body,
            timeout=10,
        )
        request.response = self  # google-auth checks request.response
        self.status = resp.status_code
        self.headers = dict(resp.headers)
        self.data = resp.content
        return self


def _find_or_create_dm_space(token: str, user_email: str) -> Optional[str]:
    """
    Set up a DM space between the Chat app and a user.
    Returns the space `name` (e.g. 'spaces/AAAA...').
    If DM already exists Google returns the existing space.
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {
            "space": {"spaceType": "DIRECT_MESSAGE"},
            "memberships": [
                {"member": {"name": f"users/{user_email}", "type": "HUMAN"}}
            ],
        }
        r = httpx.post(
            f"{_CHAT_API}/spaces:setup",
            headers=headers,
            json=body,
            timeout=15,
        )
        if r.status_code in (200, 409):
            data = r.json()
            return data.get("name")
        logger.error(f"💬 spaces:setup failed ({r.status_code}): {r.text}")
        return None
    except Exception as e:
        logger.error(f"💬 spaces:setup error: {e}")
        return None


def _send_chat_dm_sync(user_email: str, text: str):
    """Blocking DM send – called from a background thread."""
    token = _get_chat_access_token()
    if not token:
        return

    space_name = _find_or_create_dm_space(token, user_email)
    if not space_name:
        return

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        r = httpx.post(
            f"{_CHAT_API}/{space_name}/messages",
            headers=headers,
            json={"text": text},
            timeout=10,
        )
        if r.status_code == 200:
            logger.info(f"💬 Chat DM sent to {user_email}")
        else:
            logger.error(f"💬 Chat DM failed ({r.status_code}): {r.text}")
    except Exception as e:
        logger.error(f"💬 Chat DM error: {e}")


def send_chat_dm(user_email: str, text: str):
    """Fire-and-forget Chat DM to a single user."""
    if not _chat_dm_configured():
        return
    threading.Thread(
        target=_send_chat_dm_sync,
        args=(user_email, text),
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
    Notify approvers via the best available channel:
      1. Google Chat DM  (if service account configured)
      2. Email           (if SMTP configured)
    Both are tried if both are configured.
    """
    # Chat DM
    if _chat_dm_configured():
        text = f"🏰 *Approval Required*\n*{requester_name}* submitted a *{request_type}*.\n\n{detail}\n\nPlease log in to DobyHR to review."
        for u in approvers:
            if u.email:
                send_chat_dm(u.email, text)

    # Email fallback / additional
    notify_approvers_by_email(requester_name, request_type, detail, approvers)
