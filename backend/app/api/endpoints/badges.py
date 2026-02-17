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
    current_user: User = Depends(deps.get_current_gm_or_above),
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


@router.put("/{badge_id}", response_model=BadgeResponse)
def update_badge(
    badge_id: int,
    name: str = Form(...),
    description: str = Form(None),
    stat_str: int = Form(0),
    stat_def: int = Form(0),
    stat_luk: int = Form(0),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Admin edits an existing badge."""
    badge = db.query(Badge).filter(Badge.id == badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    badge.name = name
    badge.description = description
    badge.stat_str = stat_str
    badge.stat_def = stat_def
    badge.stat_luk = stat_luk

    if file:
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

    count = db.query(func.count(UserBadge.id)).filter(UserBadge.badge_id == badge.id).scalar()
    return BadgeResponse(
        id=badge.id, name=badge.name, description=badge.description,
        image=badge.image, stat_str=badge.stat_str or 0, stat_def=badge.stat_def or 0, stat_luk=badge.stat_luk or 0,
        created_at=badge.created_at, holder_count=count
    )


# ── Circle Artifact Catalog ───────────────────────────

CIRCLE_ARTIFACT_CATALOG = [
    {"id": "artifact_01", "name": "Golden Ornate Frame",      "price": 2,  "rarity": "common",    "color": "#ffd700"},
    {"id": "artifact_02", "name": "Silver Ice Crystal",       "price": 2,  "rarity": "common",    "color": "#a8d8ea"},
    {"id": "artifact_03", "name": "Emerald Vine Wreath",      "price": 3,  "rarity": "common",    "color": "#2ecc71"},
    {"id": "artifact_04", "name": "Ruby Flame Circle",        "price": 3,  "rarity": "common",    "color": "#e74c3c"},
    {"id": "artifact_05", "name": "Sapphire Water Ripple",    "price": 3,  "rarity": "uncommon",  "color": "#3498db"},
    {"id": "artifact_06", "name": "Amethyst Mystic Runes",    "price": 4,  "rarity": "uncommon",  "color": "#9b59b6"},
    {"id": "artifact_07", "name": "Bronze Dragon Coil",       "price": 4,  "rarity": "uncommon",  "color": "#cd7f32"},
    {"id": "artifact_08", "name": "Jade Serpent Ring",        "price": 4,  "rarity": "uncommon",  "color": "#00a86b"},
    {"id": "artifact_09", "name": "Obsidian Shadow Aura",     "price": 5,  "rarity": "rare",      "color": "#2c3e50"},
    {"id": "artifact_10", "name": "Celestial Star Halo",      "price": 5,  "rarity": "rare",      "color": "#f39c12"},
    {"id": "artifact_11", "name": "Phoenix Feather Crown",    "price": 5,  "rarity": "rare",      "color": "#e67e22"},
    {"id": "artifact_12", "name": "Thunderbolt Arc",          "price": 6,  "rarity": "rare",      "color": "#f1c40f"},
    {"id": "artifact_13", "name": "Moonlight Crescent",       "price": 6,  "rarity": "epic",      "color": "#bdc3c7"},
    {"id": "artifact_14", "name": "Blood Moon Eclipse",       "price": 6,  "rarity": "epic",      "color": "#c0392b"},
    {"id": "artifact_15", "name": "Crystal Prism",            "price": 7,  "rarity": "epic",      "color": "#1abc9c"},
    {"id": "artifact_16", "name": "Void Portal Swirl",        "price": 7,  "rarity": "epic",      "color": "#8e44ad"},
    {"id": "artifact_17", "name": "Ancient Tome Seal",        "price": 8,  "rarity": "legendary", "color": "#d4a44c"},
    {"id": "artifact_18", "name": "Divine Angel Wings",       "price": 8,  "rarity": "legendary", "color": "#ecf0f1"},
    {"id": "artifact_19", "name": "Demon King Crown",         "price": 9,  "rarity": "legendary", "color": "#7b241c"},
    {"id": "artifact_20", "name": "Rainbow Aurora",           "price": 10, "rarity": "mythic",    "color": "#ff6b6b"},
]

_ARTIFACT_MAP = {a["id"]: a for a in CIRCLE_ARTIFACT_CATALOG}


@router.get("/artifacts/catalog")
def get_artifact_catalog(
    current_user: User = Depends(deps.get_current_user),
):
    """Return the list of purchasable circle artifacts."""
    return CIRCLE_ARTIFACT_CATALOG


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
            "magic_background": u.magic_background or "",
            "circle_artifact": u.circle_artifact or "",
        })
    return results


# ── Magic Shop ────────────────────────────────────────

import random as _random

@router.post("/magic-shop/buy")
def buy_magic_item(
    item_type: str,
    status_text: str = None,
    artifact_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Buy a magic item from the shop. Scrolls cost 20 Gold. Artifacts cost Mana."""
    valid_items = ["scroll_of_luck", "scroll_of_strength", "scroll_of_defense", "title_scroll", "circle_artifact"]
    if item_type not in valid_items:
        raise HTTPException(status_code=400, detail=f"Invalid item. Must be one of: {valid_items}")

    result = {}
    user_name = f"{current_user.name} {current_user.surname or ''}".strip()

    # ── Circle Artifact (uses Mana) ──
    if item_type == "circle_artifact":
        if not artifact_id:
            raise HTTPException(status_code=400, detail="Please specify artifact_id")
        artifact = _ARTIFACT_MAP.get(artifact_id)
        if not artifact:
            raise HTTPException(status_code=400, detail=f"Unknown artifact: {artifact_id}")
        price = artifact["price"]
        if (current_user.angel_coins or 0) < price:
            raise HTTPException(status_code=400, detail=f"Not enough Mana! Need {price}, have {current_user.angel_coins or 0}")
        current_user.angel_coins -= price
        current_user.circle_artifact = artifact_id
        db.commit()
        return {
            "item": "Circle Artifact",
            "artifact_id": artifact_id,
            "artifact_name": artifact["name"],
            "coins": current_user.coins,
            "angel_coins": current_user.angel_coins,
        }

    # ── Gold-based items (scrolls, title) ──
    if (current_user.coins or 0) < 20:
        raise HTTPException(status_code=400, detail="Not enough Gold! (need 20)")

    if item_type == "scroll_of_luck":
        current_user.coins -= 20
        current_user.base_luk = (current_user.base_luk or 10) + 1
        log = CoinLog(
            user_id=current_user.id, amount=-20,
            reason=f"📜 Scroll of Luck — LUK +1 (now {current_user.base_luk})",
            created_by="Magic Shop"
        )
        db.add(log)
        result = {"item": "Scroll of Luck", "stat": "LUK", "new_value": current_user.base_luk, "coins": current_user.coins}

    elif item_type == "scroll_of_strength":
        current_user.coins -= 20
        current_user.base_str = (current_user.base_str or 10) + 1
        log = CoinLog(
            user_id=current_user.id, amount=-20,
            reason=f"📜 Scroll of Strength — STR +1 (now {current_user.base_str})",
            created_by="Magic Shop"
        )
        db.add(log)
        result = {"item": "Scroll of Strength", "stat": "STR", "new_value": current_user.base_str, "coins": current_user.coins}

    elif item_type == "scroll_of_defense":
        current_user.coins -= 20
        current_user.base_def = (current_user.base_def or 10) + 1
        log = CoinLog(
            user_id=current_user.id, amount=-20,
            reason=f"📜 Scroll of Defense — DEF +1 (now {current_user.base_def})",
            created_by="Magic Shop"
        )
        db.add(log)
        result = {"item": "Scroll of Defense", "stat": "DEF", "new_value": current_user.base_def, "coins": current_user.coins}

    # ── Title Scroll (uses Mana) ──
    if item_type == "title_scroll":
        if not status_text or not status_text.strip():
            raise HTTPException(status_code=400, detail="Please enter your status text!")
        TITLE_COST = 2
        if (current_user.angel_coins or 0) < TITLE_COST:
            raise HTTPException(status_code=400, detail=f"Not enough Mana! Need {TITLE_COST}")
        status_text = status_text.strip()[:70]
        current_user.angel_coins -= TITLE_COST
        current_user.status_text = status_text
        db.commit()
        return {
            "item": "Title Scroll",
            "status_text": status_text,
            "coins": current_user.coins,
            "angel_coins": current_user.angel_coins,
        }

    db.commit()
    return result


@router.delete("/{badge_id}")
def delete_badge(
    badge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
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
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Award a badge to one or more users."""
    badge = db.query(Badge).filter(Badge.id == badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    awarded = 0
    admin_name = f"{current_user.name} {current_user.surname or ''}".strip()
    awarded_names = []
    for uid in req.user_ids:
        exists = db.query(UserBadge).filter(
            UserBadge.user_id == uid, UserBadge.badge_id == badge_id
        ).first()
        if exists:
            continue
        ub = UserBadge(user_id=uid, badge_id=badge_id, awarded_by=admin_name)
        db.add(ub)
        awarded += 1
        u = db.query(User).filter(User.id == uid).first()
        if u:
            awarded_names.append(f"{u.name} {u.surname or ''}".strip())

    db.commit()

    # Webhook: badge award
    from app.services.notifications import send_town_crier_webhook
    for name in awarded_names:
        send_town_crier_webhook(f"🏅 *{name}* earned the *{badge.name}* badge!")

    return {"detail": f"Badge awarded to {awarded} user(s)"}


@router.delete("/{badge_id}/revoke/{user_id}")
def revoke_badge(
    badge_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
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
    current_user: User = Depends(deps.get_current_gm_or_above),
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
    # Matches both old format ("Received Angel Coins from ...") and new ("Received Gold/Mana from ...")
    from sqlalchemy import or_
    mana_logs = (
        db.query(CoinLog)
        .filter(or_(
            CoinLog.reason.ilike("%Received Angel Coins%"),
            CoinLog.reason.ilike("%Received Gold from%"),
            CoinLog.reason.ilike("%Received Mana from%"),
        ))
        .order_by(CoinLog.created_at.desc())
        .limit(limit)
        .all()
    )
    for ml in mana_logs:
        user = db.query(User).filter(User.id == ml.user_id).first()
        if user:
            # Extract comment from reason
            # Old: "🪽 Received Angel Coins from Name Surname: comment"
            # New: "🪽 Received Gold from Name Surname: comment"
            message = ""
            reason = ml.reason or ""
            if " from " in reason:
                after_from = reason.split(" from ", 1)[1]
                if ": " in after_from:
                    message = after_from.split(": ", 1)[1]
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

    # Step Reward claims
    from app.models.step_rewards import StepReward
    step_rewards = (
        db.query(StepReward)
        .order_by(StepReward.created_at.desc())
        .limit(limit)
        .all()
    )
    for sr in step_rewards:
        user = db.query(User).filter(User.id == sr.user_id).first()
        if user:
            reward_parts = []
            if sr.str_granted and sr.str_granted > 0:
                reward_parts.append(f"STR +{sr.str_granted}")
            if sr.coins_granted and sr.coins_granted > 0:
                reward_parts.append(f"Gold +{sr.coins_granted}")
            reward_label = ", ".join(reward_parts) if reward_parts else "Reward"
            goal_label = "Mini Daily" if sr.reward_type == "daily" else ("FULL Daily" if sr.reward_type == "daily2" else "Monthly")
            events.append({
                "id": f"step-{sr.id}",
                "type": "step_reward",
                "user_name": f"{user.name} {user.surname or ''}".strip(),
                "user_image": user.image,
                "goal_type": goal_label,
                "reward_label": reward_label,
                "timestamp": sr.created_at.isoformat() if sr.created_at else None,
            })

    # Mana Rescue events — aggregated per recipient
    rescue_logs = (
        db.query(CoinLog)
        .filter(CoinLog.reason.ilike("%Mana Rescue from%"))
        .order_by(CoinLog.created_at.desc())
        .limit(limit)
        .all()
    )
    # Group by recipient (user_id), collect rescuers
    rescue_by_user = {}
    for rl in rescue_logs:
        uid = rl.user_id
        if uid not in rescue_by_user:
            user = db.query(User).filter(User.id == uid).first()
            if not user:
                continue
            rescue_by_user[uid] = {
                "user_name": f"{user.name} {user.surname or ''}".strip(),
                "user_image": user.image,
                "rescuers": [],
                "total_gold": 0,
                "latest_ts": rl.created_at,
            }
        rescue_by_user[uid]["rescuers"].append(rl.created_by or "Unknown")
        rescue_by_user[uid]["total_gold"] += rl.amount
        if rl.created_at and rl.created_at > rescue_by_user[uid]["latest_ts"]:
            rescue_by_user[uid]["latest_ts"] = rl.created_at

    for uid, info in rescue_by_user.items():
        # Deduplicate rescuer names while preserving order
        seen = set()
        unique_rescuers = []
        for r in info["rescuers"]:
            if r not in seen:
                seen.add(r)
                unique_rescuers.append(r)
        events.append({
            "id": f"rescue-{uid}",
            "type": "rescue",
            "user_name": info["user_name"],
            "user_image": info["user_image"],
            "amount": info["total_gold"],
            "rescuers": ", ".join(unique_rescuers),
            "rescuer_count": len(info["rescuers"]),
            "timestamp": info["latest_ts"].isoformat() if info["latest_ts"] else None,
        })

    # Thank You Cards
    from app.models.social import ThankYouCard as TYC, AnonymousPraise as AP
    thank_cards = (
        db.query(TYC)
        .order_by(TYC.created_at.desc())
        .limit(limit)
        .all()
    )
    for tc in thank_cards:
        sender = db.query(User).filter(User.id == tc.sender_id).first()
        recipient = db.query(User).filter(User.id == tc.recipient_id).first()
        if sender and recipient:
            events.append({
                "id": f"thankyou-{tc.id}",
                "type": "thank_you",
                "user_name": f"{recipient.name} {recipient.surname or ''}".strip(),
                "user_image": recipient.image,
                "sender_name": f"{sender.name} {sender.surname or ''}".strip(),
                "sender_image": sender.image,
                "timestamp": tc.created_at.isoformat() if tc.created_at else None,
            })

    # Anonymous Praises
    anon_praises = (
        db.query(AP)
        .order_by(AP.created_at.desc())
        .limit(limit)
        .all()
    )
    for ap in anon_praises:
        recipient = db.query(User).filter(User.id == ap.recipient_id).first()
        if recipient:
            events.append({
                "id": f"praise-{ap.id}",
                "type": "anonymous_praise",
                "user_name": f"{recipient.name} {recipient.surname or ''}".strip(),
                "user_image": recipient.image,
                "message": ap.message,
                "timestamp": ap.created_at.isoformat() if ap.created_at else None,
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
