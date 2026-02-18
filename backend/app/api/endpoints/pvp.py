"""
PVP Arena endpoints — Admin-managed battles.
"""
import logging
import random
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.pvp import PvpBattle
from app.models.user import User, UserRole
from app.models.badge import Badge, UserBadge
from app.api import deps

logger = logging.getLogger("hr-api")
router = APIRouter(prefix="/api/pvp", tags=["PVP Arena"])
TZ7 = timezone(timedelta(hours=7))


def _player_profile(user, db):
    """Build full TownPeople-style profile for a player."""
    user_badges_rows = db.query(UserBadge).filter(UserBadge.user_id == user.id).all()
    badge_list = []
    for ub in user_badges_rows:
        badge = db.query(Badge).filter(Badge.id == ub.badge_id).first()
        if badge:
            badge_list.append({
                "id": badge.id,
                "name": badge.name,
                "image": badge.image,
            })
    return {
        "id": user.id,
        "name": user.name,
        "surname": user.surname or "",
        "position": user.position or "Adventurer",
        "image": user.image,
        "role": user.role.value if user.role else "player",
        "status_text": user.status_text or "",
        "circle_artifact": user.circle_artifact or "",
        "magic_background": user.magic_background or "",
        "coins": user.coins or 0,
        "angel_coins": user.angel_coins or 0,
        "badges": badge_list,
    }


def _get_user_total_stats(user, db):
    """Calculate total stats (base + badge bonuses) for a user."""
    badge_row = (
        db.query(
            func.coalesce(func.sum(Badge.stat_str), 0).label("s"),
            func.coalesce(func.sum(Badge.stat_def), 0).label("d"),
            func.coalesce(func.sum(Badge.stat_luk), 0).label("l"),
        )
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .filter(UserBadge.user_id == user.id)
        .first()
    )
    base_s = user.base_str if user.base_str else 10
    base_d = user.base_def if user.base_def else 10
    base_l = user.base_luk if user.base_luk else 10
    return (
        base_s + (badge_row.s if badge_row else 0),
        base_d + (badge_row.d if badge_row else 0),
        base_l + (badge_row.l if badge_row else 0),
    )


# ═══════════════════════════════════════════════════
#  Staff-facing endpoints
# ═══════════════════════════════════════════════════

@router.get("/today")
def get_today_battles(db: Session = Depends(get_db), current_user=Depends(deps.get_current_user)):
    """Get today's PVP battles with full fighter profiles."""
    now = datetime.now(TZ7)
    today = now.date()

    battles = db.query(PvpBattle).filter(PvpBattle.battle_date == today).all()

    result = []
    for b in battles:
        pa = db.query(User).filter(User.id == b.player_a_id).first()
        pb = db.query(User).filter(User.id == b.player_b_id).first()
        if not pa or not pb:
            continue

        is_resolved = b.status == "resolved"
        # Only show result after scheduled time
        if b.scheduled_time:
            is_resolved = is_resolved and now >= b.scheduled_time.replace(tzinfo=TZ7)

        result.append({
            "id": b.id,
            "battle_date": str(b.battle_date),
            "scheduled_time": b.scheduled_time.isoformat() if b.scheduled_time else None,
            "status": "resolved" if is_resolved else "scheduled",
            "player_a": _player_profile(pa, db),
            "player_b": _player_profile(pb, db),
            "winner_id": b.winner_id if is_resolved else None,
            "winner_gold": b.winner_gold or 0,
            "winner_mana": b.winner_mana or 0,
            "winner_str": b.winner_str or 0,
            "winner_def": b.winner_def or 0,
            "winner_luk": b.winner_luk or 0,
            "loser_gold": b.loser_gold or 0,
            "loser_mana": b.loser_mana or 0,
            "loser_str": b.loser_str or 0,
            "loser_def": b.loser_def or 0,
            "loser_luk": b.loser_luk or 0,
        })

    return result


@router.get("/battle/{battle_id}")
def get_battle(battle_id: int, db: Session = Depends(get_db), current_user=Depends(deps.get_current_user)):
    """Get single battle with full replay data and TownPeople-style profiles."""
    b = db.query(PvpBattle).filter(PvpBattle.id == battle_id).first()
    if not b:
        return {"error": "Battle not found"}

    now = datetime.now(TZ7)
    is_resolved = b.status == "resolved"
    if b.scheduled_time:
        is_resolved = is_resolved and now >= b.scheduled_time.replace(tzinfo=TZ7)

    pa = db.query(User).filter(User.id == b.player_a_id).first()
    pb = db.query(User).filter(User.id == b.player_b_id).first()

    pa_profile = _player_profile(pa, db)
    pb_profile = _player_profile(pb, db)
    # Inject battle stats into profile
    pa_profile.update({"str": b.a_str, "def": b.a_def, "luk": b.a_luk})
    pb_profile.update({"str": b.b_str, "def": b.b_def, "luk": b.b_luk})

    result = {
        "id": b.id,
        "battle_date": str(b.battle_date),
        "scheduled_time": b.scheduled_time.isoformat() if b.scheduled_time else None,
        "status": "resolved" if is_resolved else "scheduled",
        "player_a": pa_profile,
        "player_b": pb_profile,
        "winner_id": b.winner_id if is_resolved else None,
        "loser_id": b.loser_id if is_resolved else None,
        "battle_log": b.battle_log if is_resolved else None,
        "gold_stolen": b.gold_stolen if is_resolved else None,
        "winner_gold": b.winner_gold or 0,
        "winner_mana": b.winner_mana or 0,
        "loser_gold": b.loser_gold or 0,
        "loser_mana": b.loser_mana or 0,
    }

    return result


# ═══════════════════════════════════════════════════
#  Admin endpoints (GOD/GM only)
# ═══════════════════════════════════════════════════

class BattleMatchInput(BaseModel):
    player_a_id: int
    player_b_id: int
    scheduled_time: str  # ISO datetime string

class CreateBattlesRequest(BaseModel):
    matches: List[BattleMatchInput]
    winner_gold: int = 0
    winner_mana: int = 0
    winner_str: int = 0
    winner_def: int = 0
    winner_luk: int = 0
    loser_gold: int = 0
    loser_mana: int = 0
    loser_str: int = 0
    loser_def: int = 0
    loser_luk: int = 0


@router.get("/admin/staff")
def list_staff(db: Session = Depends(get_db), admin=Depends(deps.get_current_gm_or_above)):
    """List active staff available for battle selection."""
    users = db.query(User).all()
    result = []
    for u in users:
        s, d, l = _get_user_total_stats(u, db)
        result.append({
            "id": u.id,
            "name": u.name,
            "surname": u.surname or "",
            "image": u.image,
            "position": u.position or "",
            "str": s, "def": d, "luk": l,
        })
    return result


@router.post("/admin/random-pair")
def random_pair(db: Session = Depends(get_db), admin=Depends(deps.get_current_gm_or_above)):
    """Pick a random pair of staff."""
    users = db.query(User).all()
    if len(users) < 2:
        raise HTTPException(400, "Not enough staff")
    pair = random.sample(users, 2)
    result = []
    for u in pair:
        s, d, l = _get_user_total_stats(u, db)
        result.append({
            "id": u.id,
            "name": u.name,
            "surname": u.surname or "",
            "image": u.image,
            "position": u.position or "",
            "str": s, "def": d, "luk": l,
        })
    return result


@router.get("/admin/list")
def list_battles(db: Session = Depends(get_db), admin=Depends(deps.get_current_gm_or_above)):
    """List all upcoming/scheduled battles."""
    battles = db.query(PvpBattle).filter(
        PvpBattle.status == "scheduled"
    ).order_by(PvpBattle.scheduled_time.asc()).all()

    result = []
    for b in battles:
        pa = db.query(User).filter(User.id == b.player_a_id).first()
        pb = db.query(User).filter(User.id == b.player_b_id).first()
        result.append({
            "id": b.id,
            "battle_date": str(b.battle_date),
            "scheduled_time": b.scheduled_time.isoformat() if b.scheduled_time else None,
            "player_a": {"id": pa.id, "name": pa.name, "image": pa.image} if pa else None,
            "player_b": {"id": pb.id, "name": pb.name, "image": pb.image} if pb else None,
            "winner_gold": b.winner_gold or 0,
            "winner_mana": b.winner_mana or 0,
            "loser_gold": b.loser_gold or 0,
            "loser_mana": b.loser_mana or 0,
        })
    return result


@router.post("/admin/create")
def create_battles(req: CreateBattlesRequest, db: Session = Depends(get_db), admin=Depends(deps.get_current_gm_or_above)):
    """Create one or more battles with reward settings."""
    created = []
    for m in req.matches:
        if m.player_a_id == m.player_b_id:
            raise HTTPException(400, "Cannot match a player against themselves")

        pa = db.query(User).filter(User.id == m.player_a_id).first()
        pb = db.query(User).filter(User.id == m.player_b_id).first()
        if not pa or not pb:
            raise HTTPException(404, f"User not found: {m.player_a_id} or {m.player_b_id}")

        # Parse scheduled time
        try:
            sched = datetime.fromisoformat(m.scheduled_time)
        except ValueError:
            raise HTTPException(400, f"Invalid datetime: {m.scheduled_time}")

        a_str, a_def, a_luk = _get_user_total_stats(pa, db)
        b_str, b_def, b_luk = _get_user_total_stats(pb, db)

        battle = PvpBattle(
            battle_date=sched.date(),
            scheduled_time=sched,
            player_a_id=pa.id,
            player_b_id=pb.id,
            a_str=a_str, a_def=a_def, a_luk=a_luk,
            b_str=b_str, b_def=b_def, b_luk=b_luk,
            winner_gold=req.winner_gold,
            winner_mana=req.winner_mana,
            winner_str=req.winner_str,
            winner_def=req.winner_def,
            winner_luk=req.winner_luk,
            loser_gold=req.loser_gold,
            loser_mana=req.loser_mana,
            loser_str=req.loser_str,
            loser_def=req.loser_def,
            loser_luk=req.loser_luk,
            status="scheduled",
        )
        db.add(battle)
        created.append(f"{pa.name} vs {pb.name}")

    db.commit()
    return {"ok": True, "created": created}


@router.delete("/admin/delete/{battle_id}")
def delete_battle(battle_id: int, db: Session = Depends(get_db), admin=Depends(deps.get_current_gm_or_above)):
    """Delete a scheduled battle."""
    b = db.query(PvpBattle).filter(PvpBattle.id == battle_id).first()
    if not b:
        raise HTTPException(404, "Battle not found")
    if b.status == "resolved":
        raise HTTPException(400, "Cannot delete a resolved battle")
    db.delete(b)
    db.commit()
    return {"ok": True}

