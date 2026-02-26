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


def _player_profile(user, db, user_badges_map=None):
    """Build full TownPeople-style profile for a player."""
    badge_list = []
    if user_badges_map is not None:
        for ub in user_badges_map.get(user.id, []):
            b = ub.badge
            if b:
                badge_list.append({"id": b.id, "name": b.name, "image": b.image})
    else:
        from sqlalchemy.orm import joinedload
        user_badges_rows = (
            db.query(UserBadge)
            .options(joinedload(UserBadge.badge))
            .filter(UserBadge.user_id == user.id)
            .all()
        )
        for ub in user_badges_rows:
            if ub.badge:
                badge_list.append({"id": ub.badge.id, "name": ub.badge.name, "image": ub.badge.image})
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

@router.get("/matchmake/status")
def matchmake_status(db: Session = Depends(get_db), current_user=Depends(deps.get_current_user)):
    """Check if the current user already battled today (matchmaking)."""
    now_bkk = datetime.utcnow() + timedelta(hours=7)
    today = now_bkk.date()
    battled = db.query(PvpBattle).filter(
        PvpBattle.battle_date == today,
        PvpBattle.status == "resolved",
        PvpBattle.player_a_id == current_user.id,
    ).first()
    return {"already_battled": battled is not None, "battle_id": battled.id if battled else None}


class MatchmakeRequest(BaseModel):
    opponent_id: Optional[int] = None

@router.post("/matchmake")
def matchmake(req: MatchmakeRequest = MatchmakeRequest(), db: Session = Depends(get_db), current_user=Depends(deps.get_current_user)):
    """Staff matchmaking: fight a specific or random opponent instantly."""
    from app.scheduler import _simulate_battle
    from app.models.reward import CoinLog

    now_bkk = datetime.utcnow() + timedelta(hours=7)
    today = now_bkk.date()

    # 1. Check 1 battle/day limit
    existing = db.query(PvpBattle).filter(
        PvpBattle.battle_date == today,
        PvpBattle.status == "resolved",
        PvpBattle.player_a_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(400, "คุณต่อสู้ไปแล้ววันนี้! กลับมาใหม่พรุ่งนี้")

    # 2. Pick opponent (from frontend wheel selection, or random fallback)
    if req.opponent_id:
        opponent = db.query(User).filter(User.id == req.opponent_id).first()
        if not opponent or opponent.id == current_user.id:
            raise HTTPException(400, "Invalid opponent")
    else:
        candidates = db.query(User).filter(User.id != current_user.id).all()
        if not candidates:
            raise HTTPException(400, "ไม่มีคู่ต่อสู้")
        opponent = random.choice(candidates)

    # 3. Get stats
    a_str, a_def, a_luk = _get_user_total_stats(current_user, db)
    b_str, b_def, b_luk = _get_user_total_stats(opponent, db)

    # 4. Simulate battle instantly
    winner_side, battle_log = _simulate_battle(a_str, a_def, a_luk, b_str, b_def, b_luk)

    if winner_side == "A":
        winner, loser = current_user, opponent
    else:
        winner, loser = opponent, current_user

    # 5. Rewards / Penalties
    WINNER_GOLD = 5
    LOSER_GOLD = 5

    battle = PvpBattle(
        battle_date=today,
        scheduled_time=now_bkk,
        player_a_id=current_user.id,
        player_b_id=opponent.id,
        a_str=a_str, a_def=a_def, a_luk=a_luk,
        b_str=b_str, b_def=b_def, b_luk=b_luk,
        a_coins=current_user.coins or 0,
        a_angel_coins=current_user.angel_coins or 0,
        b_coins=opponent.coins or 0,
        b_angel_coins=opponent.angel_coins or 0,
        winner_gold=WINNER_GOLD,
        loser_gold=LOSER_GOLD,
        winner_id=winner.id,
        loser_id=loser.id,
        battle_log=battle_log,
        gold_stolen=WINNER_GOLD,
        status="resolved",
    )
    db.add(battle)

    # Apply rewards
    winner.coins = (winner.coins or 0) + WINNER_GOLD
    loser.coins = max(0, (loser.coins or 0) - LOSER_GOLD)

    # Log coins
    current_user_name = f"{current_user.name} {current_user.surname or ''}".strip()
    opponent_name = f"{opponent.name} {opponent.surname or ''}".strip()
    winner_name = f"{winner.name} {winner.surname or ''}".strip()
    loser_name = f"{loser.name} {loser.surname or ''}".strip()
    db.add(CoinLog(user_id=winner.id, amount=WINNER_GOLD, reason=f"⚔️ PvP Match: {current_user_name} vs {opponent_name} | Winner: {winner_name}", log_type="pvp", created_by="PvP Arena"))
    db.add(CoinLog(user_id=loser.id, amount=-LOSER_GOLD, reason=f"⚔️ PvP Match: {current_user_name} vs {opponent_name} | Winner: {winner_name}", log_type="pvp", created_by="PvP Arena"))

    db.commit()
    db.refresh(battle)

    logger.info(f"⚔️ Matchmake: {winner_name} beats {loser_name}")

    return {
        "battle_id": battle.id,
        "winner_id": winner.id,
        "winner_name": winner_name,
        "loser_name": loser_name,
        "opponent_id": opponent.id,
        "opponent_name": f"{opponent.name} {opponent.surname or ''}".strip(),
    }

@router.get("/today")
def get_today_battles(db: Session = Depends(get_db), current_user=Depends(deps.get_current_user)):
    """Get today's PVP battles with full fighter profiles."""
    now_bkk = datetime.utcnow() + timedelta(hours=7)
    today = now_bkk.date()

    battles = db.query(PvpBattle).filter(PvpBattle.battle_date == today).all()

    # Pre-load users and badges for all battles (eliminates N+1)
    all_player_ids = set()
    for b in battles:
        all_player_ids.add(b.player_a_id)
        all_player_ids.add(b.player_b_id)
    users_list = db.query(User).filter(User.id.in_(all_player_ids)).all() if all_player_ids else []
    user_map = {u.id: u for u in users_list}

    from sqlalchemy.orm import joinedload
    from collections import defaultdict
    all_ubs = (
        db.query(UserBadge)
        .options(joinedload(UserBadge.badge))
        .filter(UserBadge.user_id.in_(all_player_ids))
        .all()
    ) if all_player_ids else []
    ub_map = defaultdict(list)
    for ub in all_ubs:
        if ub.badge:
            ub_map[ub.user_id].append(ub)

    result = []
    for b in battles:
        pa = user_map.get(b.player_a_id)
        pb = user_map.get(b.player_b_id)
        if not pa or not pb:
            continue

        is_resolved = b.status == "resolved"
        if b.scheduled_time:
            is_resolved = is_resolved and now_bkk >= b.scheduled_time

        result.append({
            "id": b.id,
            "battle_date": str(b.battle_date),
            "scheduled_time": b.scheduled_time.isoformat() if b.scheduled_time else None,
            "status": "resolved" if is_resolved else "scheduled",
            "player_a": _player_profile(pa, db, ub_map),
            "player_b": _player_profile(pb, db, ub_map),
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

    now_bkk = datetime.utcnow() + timedelta(hours=7)
    is_resolved = b.status == "resolved"
    # Only show result after scheduled time (stored as naive Bangkok time)
    if b.scheduled_time:
        is_resolved = is_resolved and now_bkk >= b.scheduled_time

    pa = db.query(User).filter(User.id == b.player_a_id).first()
    pb = db.query(User).filter(User.id == b.player_b_id).first()

    pa_profile = _player_profile(pa, db)
    pb_profile = _player_profile(pb, db)
    # Inject battle stats into profile
    pa_profile.update({"str": b.a_str, "def": b.a_def, "luk": b.a_luk})
    pb_profile.update({"str": b.b_str, "def": b.b_def, "luk": b.b_luk})

    # For resolved battles, use fight-time snapshot coins/mana instead of live data
    if is_resolved:
        pa_profile["coins"] = b.a_coins if b.a_coins is not None else pa_profile["coins"]
        pa_profile["angel_coins"] = b.a_angel_coins if b.a_angel_coins is not None else pa_profile["angel_coins"]
        pb_profile["coins"] = b.b_coins if b.b_coins is not None else pb_profile["coins"]
        pb_profile["angel_coins"] = b.b_angel_coins if b.b_angel_coins is not None else pb_profile["angel_coins"]

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

