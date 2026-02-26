"""
Social features API: Thank You Cards, Anonymous Praise, Man of the Month.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.database import get_db
from app.models.social import ThankYouCard, AnonymousPraise, TownCrierReaction, StatBuff
from app.models.user import User
from app.models.company import Company
from app.models.reward import CoinLog
from app.models.attendance import Attendance
from app.models.expense import ExpenseRequest, ExpenseType
from app.api import deps

logger = logging.getLogger("hr-api")

router = APIRouter(prefix="/api/social", tags=["Social"])


# ── Helpers ──────────────────────────────────────────────

def _now_local():
    """Current time in UTC+7."""
    return datetime.utcnow() + timedelta(hours=7)


def _current_week_key():
    """ISO week key e.g. '2026-W08'."""
    now = _now_local()
    return f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"


def _prev_week_key():
    """ISO week key for last week."""
    prev = _now_local() - timedelta(weeks=1)
    return f"{prev.isocalendar()[0]}-W{prev.isocalendar()[1]:02d}"


def _current_date_key():
    """Date key e.g. '2026-02-17'."""
    return _now_local().strftime("%Y-%m-%d")


def _user_name(user: User):
    return f"{user.name} {user.surname or ''}".strip()


# ── Request Schemas ──────────────────────────────────────

class ThankYouRequest(BaseModel):
    recipient_id: int

class AnonymousPraiseRequest(BaseModel):
    recipient_id: int
    message: str


# ═══════════════════════════════════════════════════════════
# THANK YOU CARD
# ═══════════════════════════════════════════════════════════

@router.post("/thank-you")
def send_thank_you_card(
    req: ThankYouRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Send a Thank You Card to someone. Limited to 1 per week."""
    if req.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot send a Thank You Card to yourself!")

    recipient = db.query(User).filter(User.id == req.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    week_key = _current_week_key()

    # Check if already sent this week
    existing = db.query(ThankYouCard).filter(
        ThankYouCard.sender_id == current_user.id,
        ThankYouCard.week_key == week_key,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already sent a Thank You Card this week!")

    card = ThankYouCard(
        sender_id=current_user.id,
        recipient_id=req.recipient_id,
        week_key=week_key,
    )
    db.add(card)
    db.commit()

    sender_name = _user_name(current_user)
    recipient_name = _user_name(recipient)

    # Send Town Crier webhook
    try:
        from app.services.notifications import send_town_crier_webhook
        send_town_crier_webhook(f"💌 *{sender_name}* ส่ง Thank You Card ให้ *{recipient_name}* 💛")
    except Exception as e:
        logger.warning(f"Town Crier webhook failed: {e}")

    return {"message": f"💌 Thank You Card ถูกส่งให้ {recipient_name} แล้ว!"}


@router.get("/thank-you/status")
def get_thank_you_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Check if current user has sent a Thank You Card this week."""
    week_key = _current_week_key()
    card = db.query(ThankYouCard).filter(
        ThankYouCard.sender_id == current_user.id,
        ThankYouCard.week_key == week_key,
    ).first()

    recipient_name = None
    if card:
        recipient = db.query(User).filter(User.id == card.recipient_id).first()
        if recipient:
            recipient_name = _user_name(recipient)

    return {
        "sent_this_week": card is not None,
        "recipient_name": recipient_name,
    }


# ═══════════════════════════════════════════════════════════
# ANONYMOUS PRAISE
# ═══════════════════════════════════════════════════════════

@router.post("/anonymous-praise")
def send_anonymous_praise(
    req: AnonymousPraiseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Send an Anonymous Praise. Limited to 1 per day."""
    if req.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot praise yourself!")

    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty!")

    recipient = db.query(User).filter(User.id == req.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    date_key = _current_date_key()

    # Check if already sent today
    existing = db.query(AnonymousPraise).filter(
        AnonymousPraise.sender_id == current_user.id,
        AnonymousPraise.date_key == date_key,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already sent an Anonymous Praise today!")

    message = req.message.strip()[:200]  # Limit to 200 chars

    praise = AnonymousPraise(
        sender_id=current_user.id,
        recipient_id=req.recipient_id,
        message=message,
        date_key=date_key,
    )
    db.add(praise)
    db.commit()

    recipient_name = _user_name(recipient)

    # Send Town Crier webhook (anonymous! don't reveal sender)
    try:
        from app.services.notifications import send_town_crier_webhook
        send_town_crier_webhook(f"💬 *{recipient_name}* ถูกพูดถึงโดยบุคคลนิรนามว่า \"{message}\"")
    except Exception as e:
        logger.warning(f"Town Crier webhook failed: {e}")

    return {"message": f"💬 Anonymous Praise ถูกส่งให้ {recipient_name} แล้ว!"}


@router.get("/anonymous-praise/status")
def get_anonymous_praise_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Check if current user has sent an Anonymous Praise today."""
    date_key = _current_date_key()
    praise = db.query(AnonymousPraise).filter(
        AnonymousPraise.sender_id == current_user.id,
        AnonymousPraise.date_key == date_key,
    ).first()
    return {"sent_today": praise is not None}


# ═══════════════════════════════════════════════════════════
# MAN OF THE MONTH
# ═══════════════════════════════════════════════════════════

@router.get("/man-of-the-month")
def get_man_of_the_month(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get Man of the Month leaderboards for the current month."""
    now = _now_local()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Convert back to UTC for DB queries
    month_start_utc = month_start - timedelta(hours=7)

    results = {
        "month": now.strftime("%B %Y"),
        "most_mana_received": _leaderboard_mana_received(db, month_start_utc),
        "most_steps": _leaderboard_steps(db, now),
        "most_on_time": _leaderboard_on_time(db, month_start_utc),
        "most_gold_spent": _leaderboard_gold_spent(db, month_start_utc),
        "most_anonymous_praises": _leaderboard_anonymous_praises(db, now),
        "most_center_slips": _leaderboard_center_slips(db, month_start_utc),
    }

    # Include MOTM reward config for display
    company = db.query(Company).first()
    if company and company.motm_rewards:
        import json
        from app.models.badge import Badge
        try:
            rewards = json.loads(company.motm_rewards)
            # Resolve badge details for each category
            for cat_key, config in rewards.items():
                bid = config.get("badge_id")
                if bid:
                    badge = db.query(Badge).filter(Badge.id == int(bid)).first()
                    if badge:
                        config["badge_name"] = badge.name
                        config["badge_image"] = badge.image
                        config["badge_str"] = badge.stat_str or 0
                        config["badge_def"] = badge.stat_def or 0
                        config["badge_luk"] = badge.stat_luk or 0
                    else:
                        config["badge_name"] = f"Badge #{bid}"
            results["rewards"] = rewards
        except Exception:
            results["rewards"] = {}
    else:
        results["rewards"] = {}

    return results


def _leaderboard_mana_received(db: Session, month_start_utc):
    """Most Mana received from gifts (not admin adjust)."""
    mana_logs = (
        db.query(
            CoinLog.user_id,
            func.sum(CoinLog.amount).label("total_received"),
        )
        .filter(
            CoinLog.created_at >= month_start_utc,
            or_(
                CoinLog.reason.ilike("%Received Angel Coins%"),
                CoinLog.reason.ilike("%Received Gold from%"),
                CoinLog.reason.ilike("%Received Mana from%"),
            ),
            # Exclude admin adjustments
            ~CoinLog.created_by.ilike("%admin%"),
        )
        .group_by(CoinLog.user_id)
        .order_by(func.sum(CoinLog.amount).desc())
        .limit(10)
        .all()
    )
    return _resolve_users(db, [(r.user_id, int(r.total_received)) for r in mana_logs])


def _leaderboard_steps(db: Session, now_local):
    """Most total steps this month."""
    try:
        from app.models.fitbit import FitbitSteps
        month_start_date = now_local.replace(day=1).date()
        step_data = (
            db.query(
                FitbitSteps.user_id,
                func.sum(FitbitSteps.steps).label("total_steps"),
            )
            .filter(FitbitSteps.date >= month_start_date)
            .group_by(FitbitSteps.user_id)
            .order_by(func.sum(FitbitSteps.steps).desc())
            .limit(10)
            .all()
        )
        return _resolve_users(db, [(r.user_id, int(r.total_steps)) for r in step_data])
    except Exception as e:
        logger.warning(f"Steps leaderboard error: {e}")
        return []


def _leaderboard_on_time(db: Session, month_start_utc):
    """Most check-ins with status 'present' (on time).
    Tiebreaker: earliest average check-in time wins.
    """
    # Average seconds-since-midnight as tiebreaker (lower = earlier check-in)
    avg_time_of_day = func.avg(
        func.extract('epoch', Attendance.timestamp) % 86400
    ).label("avg_tod")

    on_time = (
        db.query(
            Attendance.user_id,
            func.count(Attendance.id).label("on_time_count"),
            avg_time_of_day,
        )
        .filter(
            Attendance.timestamp >= month_start_utc,
            Attendance.status == "present",
        )
        .group_by(Attendance.user_id)
        .order_by(
            func.count(Attendance.id).desc(),   # primary: most on-time days
            avg_time_of_day.asc(),               # tiebreaker: earliest avg check-in
        )
        .limit(10)
        .all()
    )
    return _resolve_users(db, [(r.user_id, int(r.on_time_count)) for r in on_time])


def _leaderboard_gold_spent(db: Session, month_start_utc):
    """Most Gold spent (negative coin logs, excludes penalties like 'Late penalty', 'Absent penalty')."""
    spending_logs = (
        db.query(
            CoinLog.user_id,
            func.sum(func.abs(CoinLog.amount)).label("total_spent"),
        )
        .filter(
            CoinLog.created_at >= month_start_utc,
            CoinLog.amount < 0,
            ~CoinLog.reason.ilike("%penalty%"),
            ~CoinLog.reason.ilike("%Late%"),
            ~CoinLog.reason.ilike("%Absent%"),
        )
        .group_by(CoinLog.user_id)
        .order_by(func.sum(func.abs(CoinLog.amount)).desc())
        .limit(10)
        .all()
    )
    return _resolve_users(db, [(r.user_id, int(r.total_spent)) for r in spending_logs])


def _leaderboard_anonymous_praises(db: Session, now_local):
    """Most Anonymous Praises received this month."""
    month_str = now_local.strftime("%Y-%m")  # e.g. "2026-02"
    praises = (
        db.query(
            AnonymousPraise.recipient_id,
            func.count(AnonymousPraise.id).label("praise_count"),
        )
        .filter(AnonymousPraise.date_key.startswith(month_str))
        .group_by(AnonymousPraise.recipient_id)
        .order_by(func.count(AnonymousPraise.id).desc())
        .limit(10)
        .all()
    )
    return _resolve_users(db, [(r.recipient_id, int(r.praise_count)) for r in praises])


def _leaderboard_center_slips(db: Session, month_start_utc):
    """Most Center Expense slips submitted this month."""
    slips = (
        db.query(
            ExpenseRequest.submitted_by_id,
            func.count(ExpenseRequest.id).label("slip_count"),
        )
        .filter(
            ExpenseRequest.created_at >= month_start_utc,
            ExpenseRequest.expense_type == ExpenseType.CENTER,
            ExpenseRequest.submitted_by_id.isnot(None),
        )
        .group_by(ExpenseRequest.submitted_by_id)
        .order_by(func.count(ExpenseRequest.id).desc())
        .limit(10)
        .all()
    )
    return _resolve_users(db, [(r.submitted_by_id, int(r.slip_count)) for r in slips])


def _resolve_users(db: Session, user_value_pairs):
    """Convert [(user_id, value)] to list of dicts with user info."""
    results = []
    for uid, value in user_value_pairs:
        user = db.query(User).filter(User.id == uid).first()
        if user:
            results.append({
                "user_id": user.id,
                "name": user.name,
                "surname": user.surname or "",
                "image": user.image,
                "position": user.position or "",
                "value": value,
            })
    return results


# ═══════════════════════════════════════════════════════════
# TOWN CRIER REACTIONS
# ═══════════════════════════════════════════════════════════

ALLOWED_EMOJIS = ["❤️", "👏", "🎉"]

class ReactionRequest(BaseModel):
    event_id: str   # e.g. "badge-42"
    emoji: str      # e.g. "❤️"

@router.post("/reactions")
def toggle_reaction(
    req: ReactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Toggle a reaction on a Town Crier event. If already exists, remove it."""
    if req.emoji not in ALLOWED_EMOJIS:
        raise HTTPException(400, f"Emoji must be one of {ALLOWED_EMOJIS}")

    existing = db.query(TownCrierReaction).filter(
        TownCrierReaction.event_id == req.event_id,
        TownCrierReaction.user_id == current_user.id,
        TownCrierReaction.emoji == req.emoji,
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"action": "removed"}
    else:
        r = TownCrierReaction(event_id=req.event_id, user_id=current_user.id, emoji=req.emoji)
        db.add(r)
        db.commit()
        return {"action": "added", "id": r.id}


@router.get("/reactions")
def get_reactions(
    event_ids: str = "",   # comma-separated event IDs
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get reactions for multiple events (batch load for Town Crier)."""
    if not event_ids:
        return {}

    ids = [eid.strip() for eid in event_ids.split(",") if eid.strip()]
    if not ids:
        return {}

    reactions = db.query(TownCrierReaction).filter(
        TownCrierReaction.event_id.in_(ids)
    ).all()

    # Group by event_id → {emoji: {count, reacted}}
    result = {}
    for eid in ids:
        result[eid] = {}

    for r in reactions:
        eid = r.event_id
        if eid not in result:
            result[eid] = {}
        if r.emoji not in result[eid]:
            result[eid][r.emoji] = {"count": 0, "reacted": False}
        result[eid][r.emoji]["count"] += 1
        if r.user_id == current_user.id:
            result[eid][r.emoji]["reacted"] = True

    return result


# ═══════════════════════════════════════════════════════════
# STAT BUFFS
# ═══════════════════════════════════════════════════════════

class BuffRequest(BaseModel):
    recipient_id: int
    stat_type: str   # "str", "def", "luk"
    amount: int      # number of Mana to spend (= stat points)

@router.post("/buff")
def send_buff(
    req: BuffRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Send a temporary stat buff using Mana. 1 Mana = 1 stat point, expires at midnight."""
    if req.stat_type not in ("str", "def", "luk"):
        raise HTTPException(400, "stat_type must be str, def, or luk")
    if req.amount < 1:
        raise HTTPException(400, "amount must be at least 1")
    if req.recipient_id == current_user.id:
        raise HTTPException(400, "You cannot buff yourself!")

    recipient = db.query(User).filter(User.id == req.recipient_id).first()
    if not recipient:
        raise HTTPException(404, "Recipient not found")

    # Check Mana balance
    if (current_user.angel_coins or 0) < req.amount:
        raise HTTPException(400, "Not enough Mana!")

    # Deduct Mana
    current_user.angel_coins -= req.amount

    # Create buff
    date_key = _current_date_key()
    buff = StatBuff(
        sender_id=current_user.id,
        recipient_id=req.recipient_id,
        stat_type=req.stat_type,
        amount=req.amount,
        date_key=date_key,
    )
    db.add(buff)

    # Log
    stat_icons = {"str": "⚔️", "def": "🛡️", "luk": "🍀"}
    icon = stat_icons.get(req.stat_type, "⚡")
    sender_name = _user_name(current_user)
    recipient_name = _user_name(recipient)

    db.add(CoinLog(
        user_id=current_user.id,
        amount=-req.amount,
        reason=f"⚡ Buff {icon} {req.stat_type.upper()}+{req.amount} → {recipient_name}",
        created_by=sender_name,
    ))

    db.commit()

    return {"message": f"⚡ {icon} {req.stat_type.upper()}+{req.amount} buff sent to {recipient_name}!"}


@router.get("/buff/active")
def get_active_buffs(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get active buffs for a user (today only). Defaults to current user."""
    target_id = user_id or current_user.id
    date_key = _current_date_key()

    buffs = db.query(StatBuff).filter(
        StatBuff.recipient_id == target_id,
        StatBuff.date_key == date_key,
    ).all()

    totals = {"str": 0, "def": 0, "luk": 0}
    details = []
    for b in buffs:
        totals[b.stat_type] = totals.get(b.stat_type, 0) + b.amount
        sender = db.query(User).filter(User.id == b.sender_id).first()
        details.append({
            "id": b.id,
            "sender_name": _user_name(sender) if sender else "?",
            "stat_type": b.stat_type,
            "amount": b.amount,
        })

    return {"totals": totals, "details": details}

