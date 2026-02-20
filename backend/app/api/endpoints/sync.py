"""
Sync endpoints — receive Badge / Badge Quest data from another environment.
Authenticated via X-Sync-Key header (shared secret).
"""
import os
import uuid
import shutil
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.badge import Badge
from app.models.badge_quest import BadgeQuest

router = APIRouter(prefix="/api/sync", tags=["Sync"])


# ── Auth ──────────────────────────────────────────────
def _verify_sync_key(x_sync_key: str = Header(...)):
    """Validate the shared sync API key."""
    if not settings.SYNC_API_KEY:
        raise HTTPException(status_code=503, detail="Sync not configured on this server")
    if x_sync_key != settings.SYNC_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid sync key")
    return True


# ── Badge Sync (upsert) ─────────────────────────────
@router.post("/badge")
def sync_badge(
    name: str = Form(...),
    description: str = Form(None),
    stat_str: int = Form(0),
    stat_def: int = Form(0),
    stat_luk: int = Form(0),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    _auth: bool = Depends(_verify_sync_key),
):
    """Receive a badge from another environment (upsert by name)."""
    badge = db.query(Badge).filter(Badge.name == name).first()

    if badge:
        # Update existing
        badge.description = description
        badge.stat_str = stat_str
        badge.stat_def = stat_def
        badge.stat_luk = stat_luk
        action = "updated"
    else:
        # Create new
        badge = Badge(
            name=name,
            description=description,
            stat_str=stat_str,
            stat_def=stat_def,
            stat_luk=stat_luk,
        )
        db.add(badge)
        action = "created"

    # Handle image upload
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1]
        filename = f"badge_{uuid.uuid4().hex[:8]}{ext}"
        upload_dir = os.path.join(settings.UPLOAD_DIR, "badges")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        badge.image = f"/uploads/badges/{filename}"

    db.commit()
    db.refresh(badge)

    return {
        "action": action,
        "badge_id": badge.id,
        "name": badge.name,
        "image": badge.image,
    }


# ── Badge Quest Sync ─────────────────────────────────
class QuestSyncPayload(BaseModel):
    badge_name: Optional[str] = None      # resolved to badge_id on this server
    condition_query: Optional[str] = None
    condition_type: Optional[str] = None
    threshold: Optional[int] = None
    is_active: bool = True
    description: Optional[str] = None
    max_awards: Optional[int] = None
    reward_type: Optional[str] = "badge"
    reward_value: Optional[int] = 0


@router.post("/badge-quest")
def sync_badge_quest(
    body: QuestSyncPayload,
    db: Session = Depends(get_db),
    _auth: bool = Depends(_verify_sync_key),
):
    """Receive a badge quest from another environment."""
    badge_id = None

    # Resolve badge by name if reward_type is badge
    if body.reward_type == "badge" and body.badge_name:
        badge = db.query(Badge).filter(Badge.name == body.badge_name).first()
        if not badge:
            raise HTTPException(
                status_code=404,
                detail=f"Badge '{body.badge_name}' not found on this server. Push the badge first.",
            )
        badge_id = badge.id

    quest = BadgeQuest(
        badge_id=badge_id,
        condition_query=body.condition_query,
        condition_type=body.condition_type if not body.condition_query else None,
        threshold=body.threshold if not body.condition_query else None,
        is_active=body.is_active,
        description=body.description,
        max_awards=body.max_awards,
        reward_type=body.reward_type,
        reward_value=body.reward_value or 0,
    )
    db.add(quest)
    db.commit()
    db.refresh(quest)

    return {"quest_id": quest.id, "message": "Quest synced", "badge_id": badge_id}
