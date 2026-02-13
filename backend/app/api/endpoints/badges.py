import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.config import settings
from app.models.badge import Badge, UserBadge
from app.models.user import User
from app.models.reward import CoinLog
from app.schemas.badge import BadgeCreate, BadgeResponse, UserBadgeResponse, AwardBadgeRequest, UserStatsResponse
from app.api import deps

router = APIRouter(prefix="/api/badges", tags=["Badges"])


# ── CRUD ──────────────────────────────────────────────

@router.get("", response_model=List[BadgeResponse])
def get_all_badges(db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_user)):
    """List all badges with holder count."""
    badges = db.query(Badge).order_by(Badge.created_at.desc()).all()
    results = []
    for b in badges:
        count = db.query(func.count(UserBadge.id)).filter(UserBadge.badge_id == b.id).scalar()
        results.append(BadgeResponse(
            id=b.id, name=b.name, description=b.description,
            image=b.image, stat_str=b.stat_str or 0, stat_def=b.stat_def or 0, stat_luk=b.stat_luk or 0,
            created_at=b.created_at, holder_count=count
        ))
    return results


@router.post("", response_model=BadgeResponse)
def create_badge(
    name: str = Form(...),
    description: str = Form(None),
    stat_str: int = Form(0),
    stat_def: int = Form(0),
    stat_luk: int = Form(0),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_admin),
):
    """Admin creates a new badge with optional image upload and stat bonuses."""
    badge = Badge(name=name, description=description, stat_str=stat_str, stat_def=stat_def, stat_luk=stat_luk)

    if file:
        ext = os.path.splitext(file.filename)[1]
        filename = f"badge_{uuid.uuid4().hex[:8]}{ext}"
        upload_dir = os.path.join(settings.UPLOAD_DIR, "badges")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        badge.image = f"/uploads/badges/{filename}"

    db.add(badge)
    db.commit()
    db.refresh(badge)
    return BadgeResponse(
        id=badge.id, name=badge.name, description=badge.description,
        image=badge.image, stat_str=badge.stat_str or 0, stat_def=badge.stat_def or 0, stat_luk=badge.stat_luk or 0,
        created_at=badge.created_at, holder_count=0
    )


# ── Town People (staff directory with stats) ──────────

@router.get("/town-people")
def get_town_people(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get all active staff with profile, stats, badges, coins, and mana."""
    staff = db.query(User).all()
    results = []
    for u in staff:
        user_badges_rows = db.query(UserBadge).filter(UserBadge.user_id == u.id).all()
        badge_str = badge_def = badge_luk = 0
        badge_list = []
        for ub in user_badges_rows:
            badge = db.query(Badge).filter(Badge.id == ub.badge_id).first()
            if badge:
                badge_str += badge.stat_str or 0
                badge_def += badge.stat_def or 0
                badge_luk += badge.stat_luk or 0
                badge_list.append({
                    "id": badge.id,
                    "name": badge.name,
                    "description": badge.description or "",
                    "image": badge.image,
                    "bonus_str": badge.stat_str or 0,
                    "bonus_def": badge.stat_def or 0,
                    "bonus_luk": badge.stat_luk or 0,
                })
        base_s = u.base_str if hasattr(u, 'base_str') and u.base_str else 10
        base_d = u.base_def if hasattr(u, 'base_def') and u.base_def else 10
        base_l = u.base_luk if hasattr(u, 'base_luk') and u.base_luk else 10
        results.append({
            "id": u.id,
            "name": u.name,
            "surname": u.surname or "",
            "position": u.position or "Adventurer",
            "department": u.department,
            "image": u.image,
            "coins": u.coins or 0,
            "angel_coins": u.angel_coins or 0,
            "role": u.role.value if u.role else "staff",
            "stats": {
                "total_str": base_s + badge_str,
                "total_def": base_d + badge_def,
                "total_luk": base_l + badge_luk,
            },
            "badges": badge_list,
            "status_text": u.status_text or "",
        })
    return results


# ── Magic Shop ────────────────────────────────────────

import random as _random

@router.post("/magic-shop/buy")
def buy_magic_item(
    item_type: str,
    status_text: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Buy a magic item from the shop. All items cost 1 Gold."""
    valid_items = ["magic_lottery", "scroll_of_luck", "scroll_of_strength", "scroll_of_defense", "title_scroll"]
    if item_type not in valid_items:
        raise HTTPException(status_code=400, detail=f"Invalid item. Must be one of: {valid_items}")

    if (current_user.coins or 0) < 1:
        raise HTTPException(status_code=400, detail="Not enough Gold!")

    result = {}
    user_name = f"{current_user.name} {current_user.surname or ''}".strip()

    if item_type == "magic_lottery":
        if (current_user.coins or 0) < 3:
            raise HTTPException(status_code=400, detail="Not enough Gold! Magic Lottery costs 3 Gold.")
        # Limit: 1 per day per person (UTC+7)
        from datetime import datetime, timedelta, timezone
        tz7 = timezone(timedelta(hours=7))
        now = datetime.now(tz7)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).replace(tzinfo=None)
        already_played = db.query(CoinLog).filter(
            CoinLog.user_id == current_user.id,
            CoinLog.reason.ilike("%Magic Lottery%"),
            CoinLog.created_at >= today_start,
        ).first()
        if already_played:
            raise HTTPException(status_code=400, detail="You already played Magic Lottery today! Come back tomorrow 🎲")
        current_user.coins -= 3
        won = _random.randint(-6, 8)
        gained = max(0, won)  # Can't have negative coins
        current_user.coins += gained
        log = CoinLog(
            user_id=current_user.id,
            amount=won - 3,
            reason=f"🎲 Magic Lottery! Spent 3 Gold, result: {won} Gold",
            created_by="Magic Shop"
        )
        db.add(log)
        result = {"item": "Magic Lottery", "won": won, "net": won - 3, "coins": current_user.coins}

    elif item_type == "scroll_of_luck":
        current_user.coins -= 1
        current_user.base_luk = (current_user.base_luk or 10) + 1
        log = CoinLog(
            user_id=current_user.id, amount=-1,
            reason=f"📜 Scroll of Luck — LUK +1 (now {current_user.base_luk})",
            created_by="Magic Shop"
        )
        db.add(log)
        result = {"item": "Scroll of Luck", "stat": "LUK", "new_value": current_user.base_luk, "coins": current_user.coins}

    elif item_type == "scroll_of_strength":
        current_user.coins -= 1
        current_user.base_str = (current_user.base_str or 10) + 1
        log = CoinLog(
            user_id=current_user.id, amount=-1,
            reason=f"📜 Scroll of Strength — STR +1 (now {current_user.base_str})",
            created_by="Magic Shop"
        )
        db.add(log)
        result = {"item": "Scroll of Strength", "stat": "STR", "new_value": current_user.base_str, "coins": current_user.coins}

    elif item_type == "scroll_of_defense":
        current_user.coins -= 1
        current_user.base_def = (current_user.base_def or 10) + 1
        log = CoinLog(
            user_id=current_user.id, amount=-1,
            reason=f"📜 Scroll of Defense — DEF +1 (now {current_user.base_def})",
            created_by="Magic Shop"
        )
        db.add(log)
        result = {"item": "Scroll of Defense", "stat": "DEF", "new_value": current_user.base_def, "coins": current_user.coins}

    elif item_type == "title_scroll":
        if not status_text or not status_text.strip():
            raise HTTPException(status_code=400, detail="Please enter your status text!")
        status_text = status_text.strip()[:70]
        current_user.coins -= 1
        current_user.status_text = status_text
        log = CoinLog(
            user_id=current_user.id, amount=-1,
            reason=f"📜 Title Scroll — Status: \"{status_text}\"",
            created_by="Magic Shop"
        )
        db.add(log)
        result = {"item": "Title Scroll", "status_text": status_text, "coins": current_user.coins}

    db.commit()
    return result


@router.delete("/{badge_id}")
def delete_badge(
    badge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_admin),
):
    badge = db.query(Badge).filter(Badge.id == badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")
    db.delete(badge)
    db.commit()
    return {"detail": "Badge deleted"}


# ── Award / Revoke ────────────────────────────────────

@router.post("/{badge_id}/award")
def award_badge(
    badge_id: int,
    req: AwardBadgeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_admin),
):
    """Award a badge to one or more users."""
    badge = db.query(Badge).filter(Badge.id == badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    awarded = 0
    admin_name = f"{current_user.name} {current_user.surname or ''}".strip()
    for uid in req.user_ids:
        exists = db.query(UserBadge).filter(
            UserBadge.user_id == uid, UserBadge.badge_id == badge_id
        ).first()
        if exists:
            continue
        ub = UserBadge(user_id=uid, badge_id=badge_id, awarded_by=admin_name)
        db.add(ub)
        awarded += 1

    db.commit()
    return {"detail": f"Badge awarded to {awarded} user(s)"}


@router.delete("/{badge_id}/revoke/{user_id}")
def revoke_badge(
    badge_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_admin),
):
    ub = db.query(UserBadge).filter(
        UserBadge.user_id == user_id, UserBadge.badge_id == badge_id
    ).first()
    if not ub:
        raise HTTPException(status_code=404, detail="User badge not found")
    db.delete(ub)
    db.commit()
    return {"detail": "Badge revoked"}


# ── Get badge holders ─────────────────────────────────

@router.get("/{badge_id}/holders")
def get_badge_holders(
    badge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_admin),
):
    """Get all users who hold a specific badge."""
    holders = db.query(UserBadge).filter(UserBadge.badge_id == badge_id).all()
    results = []
    for ub in holders:
        user = db.query(User).filter(User.id == ub.user_id).first()
        results.append({
            "user_id": ub.user_id,
            "user_name": f"{user.name} {user.surname or ''}".strip() if user else f"User #{ub.user_id}",
            "user_image": user.image if user else None,
            "awarded_at": ub.awarded_at.isoformat() if ub.awarded_at else None,
            "awarded_by": ub.awarded_by,
        })
    return results


# ── User badge endpoints ──────────────────────────────

def _build_user_badge_response(ub, badge):
    return UserBadgeResponse(
        id=ub.id, badge_id=badge.id, badge_name=badge.name,
        badge_image=badge.image, badge_description=badge.description,
        stat_str=badge.stat_str or 0, stat_def=badge.stat_def or 0, stat_luk=badge.stat_luk or 0,
        awarded_at=ub.awarded_at, awarded_by=ub.awarded_by
    )


@router.get("/user/me", response_model=List[UserBadgeResponse])
def get_my_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get current user's badges."""
    user_badges = db.query(UserBadge).filter(UserBadge.user_id == current_user.id).all()
    results = []
    for ub in user_badges:
        badge = db.query(Badge).filter(Badge.id == ub.badge_id).first()
        if badge:
            results.append(_build_user_badge_response(ub, badge))
    return results


@router.get("/user/{user_id}", response_model=List[UserBadgeResponse])
def get_user_badges(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get badges for a specific user."""
    user_badges = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
    results = []
    for ub in user_badges:
        badge = db.query(Badge).filter(Badge.id == ub.badge_id).first()
        if badge:
            results.append(_build_user_badge_response(ub, badge))
    return results


# ── Recent awards (company-wide) ─────────────────────

@router.get("/awards/recent")
def get_recent_awards(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Unified Town Crier feed: badge awards + mana transfers."""
    events = []

    # Badge awards
    recent_badges = (
        db.query(UserBadge)
        .order_by(UserBadge.awarded_at.desc())
        .limit(limit)
        .all()
    )
    for ub in recent_badges:
        badge = db.query(Badge).filter(Badge.id == ub.badge_id).first()
        user = db.query(User).filter(User.id == ub.user_id).first()
        if badge and user:
            events.append({
                "id": f"badge-{ub.id}",
                "type": "badge",
                "user_name": f"{user.name} {user.surname or ''}".strip(),
                "user_image": user.image,
                "badge_name": badge.name,
                "badge_image": badge.image,
                "timestamp": ub.awarded_at.isoformat() if ub.awarded_at else None,
                "detail": ub.awarded_by,
            })

    # Mana (Angel Coin) transfers — only "Received" entries
    mana_logs = (
        db.query(CoinLog)
        .filter(CoinLog.reason.ilike("%Received Angel Coins%"))
        .order_by(CoinLog.created_at.desc())
        .limit(limit)
        .all()
    )
    for ml in mana_logs:
        user = db.query(User).filter(User.id == ml.user_id).first()
        if user:
            # Extract message from reason (format: "... from Name Surname: message")
            message = ""
            if ml.reason and ": " in ml.reason:
                parts = ml.reason.split(": ", 1)
                if len(parts) > 1:
                    # The first ": " after sender name is the comment
                    # Reason format: "🪽 Received Angel Coins from Name Surname: comment"
                    message = parts[1]
            events.append({
                "id": f"mana-{ml.id}",
                "type": "mana",
                "user_name": f"{user.name} {user.surname or ''}".strip(),
                "user_image": user.image,
                "amount": ml.amount,
                "reason": ml.reason,
                "message": message,
                "timestamp": ml.created_at.isoformat() if ml.created_at else None,
                "detail": ml.created_by,
            })

    # Lucky Draw winners
    draw_logs = (
        db.query(CoinLog)
        .filter(CoinLog.reason.ilike("%Lucky Draw%"))
        .order_by(CoinLog.created_at.desc())
        .limit(limit)
        .all()
    )
    for dl in draw_logs:
        user = db.query(User).filter(User.id == dl.user_id).first()
        if user:
            events.append({
                "id": f"draw-{dl.id}",
                "type": "lucky_draw",
                "user_name": f"{user.name} {user.surname or ''}".strip(),
                "user_image": user.image,
                "amount": dl.amount,
                "reason": dl.reason,
                "timestamp": dl.created_at.isoformat() if dl.created_at else None,
                "detail": "Lucky Draw",
            })

    # Magic Lottery results
    lottery_logs = (
        db.query(CoinLog)
        .filter(CoinLog.reason.ilike("%Magic Lottery%"))
        .order_by(CoinLog.created_at.desc())
        .limit(limit)
        .all()
    )
    for ll in lottery_logs:
        user = db.query(User).filter(User.id == ll.user_id).first()
        if user:
            events.append({
                "id": f"lottery-{ll.id}",
                "type": "magic_lottery",
                "user_name": f"{user.name} {user.surname or ''}".strip(),
                "user_image": user.image,
                "amount": ll.amount,
                "reason": ll.reason,
                "timestamp": ll.created_at.isoformat() if ll.created_at else None,
                "detail": "Magic Shop",
            })

    # Sort combined by timestamp desc and return top N
    events.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
    return events[:limit]


# ── Stats ─────────────────────────────────────────────

@router.get("/stats/me", response_model=UserStatsResponse)
def get_my_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get current user's total stats (base + badge bonuses)."""
    return _compute_user_stats(current_user, db)


@router.get("/stats/{user_id}", response_model=UserStatsResponse)
def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get a user's total stats."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _compute_user_stats(user, db)




def _compute_user_stats(user: User, db: Session) -> UserStatsResponse:
    user_badges = db.query(UserBadge).filter(UserBadge.user_id == user.id).all()
    badge_str = badge_def = badge_luk = 0
    for ub in user_badges:
        badge = db.query(Badge).filter(Badge.id == ub.badge_id).first()
        if badge:
            badge_str += badge.stat_str or 0
            badge_def += badge.stat_def or 0
            badge_luk += badge.stat_luk or 0

    base_s = user.base_str if hasattr(user, 'base_str') and user.base_str else 10
    base_d = user.base_def if hasattr(user, 'base_def') and user.base_def else 10
    base_l = user.base_luk if hasattr(user, 'base_luk') and user.base_luk else 10

    return UserStatsResponse(
        base_str=base_s, base_def=base_d, base_luk=base_l,
        badge_str=badge_str, badge_def=badge_def, badge_luk=badge_luk,
        total_str=base_s + badge_str, total_def=base_d + badge_def, total_luk=base_l + badge_luk,
    )
