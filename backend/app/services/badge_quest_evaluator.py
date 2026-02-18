"""
Badge Quest condition evaluators — query-based system.

Supports SQL-like queries, e.g.:
    total_steps >= 50
    mana_sent > 3 AND mana_received > 5
    checkin_streak >= 10 OR total_steps > 1000
    item_6 >= 3          (bought item #6 at least 3 times)
    leave_sick >= 1       (took sick leave at least once)

Each "field" maps to a resolver function that computes the user's value.
"""
import re
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.attendance import Attendance
from app.models.fitbit import FitbitSteps
from app.models.reward import CoinLog, Redemption, Reward
from app.models.leave import LeaveRequest
from app.models.badge import UserBadge
from app.models.pvp import PvpBattle
from app.models.social import ThankYouCard, AnonymousPraise

logger = logging.getLogger("hr-api")

BKK = timezone(timedelta(hours=7))

# ── Field Resolvers ───────────────────────────────────
# Each takes (user_id, db) → int


def _resolve_checkin_streak(user_id: int, db: Session) -> int:
    records = (
        db.query(Attendance)
        .filter(Attendance.user_id == user_id, Attendance.status == "present")
        .order_by(Attendance.timestamp.desc())
        .all()
    )
    seen_dates = set()
    for r in records:
        local_dt = r.timestamp + timedelta(hours=7) if r.timestamp else None
        if local_dt:
            seen_dates.add(local_dt.date())
    today = (datetime.utcnow() + timedelta(hours=7)).date()
    streak = 0
    d = today
    while d in seen_dates:
        streak += 1
        d -= timedelta(days=1)
    return streak


def _resolve_total_steps(user_id: int, db: Session) -> int:
    return (
        db.query(func.coalesce(func.sum(FitbitSteps.steps), 0))
        .filter(FitbitSteps.user_id == user_id)
        .scalar()
    )


def _resolve_mana_received(user_id: int, db: Session) -> int:
    from sqlalchemy import or_
    return (
        db.query(func.count(CoinLog.id))
        .filter(CoinLog.user_id == user_id, or_(
            CoinLog.reason.ilike("%Received Angel Coins%"),
            CoinLog.reason.ilike("%Received Gold from%"),
            CoinLog.reason.ilike("%Received Mana from%"),
        ))
        .scalar()
    )


def _resolve_mana_sent(user_id: int, db: Session) -> int:
    from sqlalchemy import or_
    return (
        db.query(func.count(CoinLog.id))
        .filter(CoinLog.user_id == user_id, or_(
            CoinLog.reason.ilike("%Sent%Angel Coins%"),
            CoinLog.reason.ilike("%Sent%Mana as%"),
        ))
        .scalar()
    )


def _resolve_revival_prayers(user_id: int, db: Session) -> int:
    """How many times this user contributed a Revival Prayer."""
    return (
        db.query(func.count(CoinLog.id))
        .filter(CoinLog.reason.ilike(f"%Revival Prayer from {db.query(User).filter(User.id == user_id).first().name if db.query(User).filter(User.id == user_id).first() else ''}%"))
        .scalar()
    )


def _resolve_scroll_purchased(user_id: int, db: Session) -> int:
    return (
        db.query(func.count(CoinLog.id))
        .filter(CoinLog.user_id == user_id, CoinLog.reason.ilike("%Scroll of%"))
        .scalar()
    )


def _resolve_user_field(field_name: str):
    """Factory for simple User column resolvers."""
    def resolver(user_id: int, db: Session) -> int:
        user = db.query(User).filter(User.id == user_id).first()
        return getattr(user, field_name, 0) or 0 if user else 0
    return resolver


# ── Item purchase resolvers (dynamic: item_<id>) ─────

def _resolve_item_purchased(reward_id: int):
    """Factory: count how many times user redeemed a specific item (non-rejected)."""
    def resolver(user_id: int, db: Session) -> int:
        return (
            db.query(func.count(Redemption.id))
            .filter(
                Redemption.user_id == user_id,
                Redemption.reward_id == reward_id,
                Redemption.status != "rejected",
            )
            .scalar()
        )
    return resolver


def _resolve_total_redemptions(user_id: int, db: Session) -> int:
    """Total items redeemed (non-rejected)."""
    return (
        db.query(func.count(Redemption.id))
        .filter(
            Redemption.user_id == user_id,
            Redemption.status != "rejected",
        )
        .scalar()
    )


# ── Leave resolvers ──────────────────────────────────

def _resolve_leave(leave_type: str):
    """Factory: count approved leaves of a specific type."""
    def resolver(user_id: int, db: Session) -> int:
        return (
            db.query(func.count(LeaveRequest.id))
            .filter(
                LeaveRequest.user_id == user_id,
                LeaveRequest.leave_type == leave_type,
                LeaveRequest.status == "approved",
            )
            .scalar()
        )
    return resolver


# ── Registry ──────────────────────────────────────────

def _resolve_rescue_given(user_id: int, db: Session) -> int:
    """How many times this user contributed a Revival Prayer to help someone."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return 0
    user_name = f"{user.name} {user.surname or ''}".strip()
    return db.query(func.count(CoinLog.id)).filter(
        CoinLog.reason.ilike(f"%Revival Prayer from {user_name}%"),
    ).scalar()


def _resolve_rescue_received(user_id: int, db: Session) -> int:
    """How many times this user was successfully revived."""
    return db.query(func.count(CoinLog.id)).filter(
        CoinLog.user_id == user_id,
        CoinLog.reason.ilike("💖 Revived by%"),
    ).scalar()


# ── New resolvers ────────────────────────────────────

def _resolve_total_checkins(user_id: int, db: Session) -> int:
    """Total number of check-ins (any status)."""
    return db.query(func.count(Attendance.id)).filter(
        Attendance.user_id == user_id,
    ).scalar()


def _resolve_on_time_checkins(user_id: int, db: Session) -> int:
    """Number of on-time check-ins (status = 'present')."""
    return db.query(func.count(Attendance.id)).filter(
        Attendance.user_id == user_id,
        Attendance.status == "present",
    ).scalar()


def _resolve_pvp_wins(user_id: int, db: Session) -> int:
    """Number of PvP battles won."""
    return db.query(func.count(PvpBattle.id)).filter(
        PvpBattle.winner_id == user_id,
    ).scalar()


def _resolve_pvp_battles(user_id: int, db: Session) -> int:
    """Total PvP battles played (as player A or B)."""
    from sqlalchemy import or_
    return db.query(func.count(PvpBattle.id)).filter(
        or_(PvpBattle.player_a_id == user_id, PvpBattle.player_b_id == user_id),
    ).scalar()


def _resolve_thank_you_sent(user_id: int, db: Session) -> int:
    """Thank You Cards sent."""
    return db.query(func.count(ThankYouCard.id)).filter(
        ThankYouCard.sender_id == user_id,
    ).scalar()


def _resolve_thank_you_received(user_id: int, db: Session) -> int:
    """Thank You Cards received."""
    return db.query(func.count(ThankYouCard.id)).filter(
        ThankYouCard.recipient_id == user_id,
    ).scalar()


def _resolve_anonymous_praise_sent(user_id: int, db: Session) -> int:
    """Anonymous praises written."""
    return db.query(func.count(AnonymousPraise.id)).filter(
        AnonymousPraise.sender_id == user_id,
    ).scalar()


def _resolve_anonymous_praise_received(user_id: int, db: Session) -> int:
    """Anonymous praises received."""
    return db.query(func.count(AnonymousPraise.id)).filter(
        AnonymousPraise.recipient_id == user_id,
    ).scalar()


def _resolve_fortune_spins(user_id: int, db: Session) -> int:
    """Total Fortune Wheel spins."""
    return db.query(func.count(CoinLog.id)).filter(
        CoinLog.user_id == user_id,
        CoinLog.reason.ilike("%Magic Lottery%"),
    ).scalar()


def _resolve_badges_count(user_id: int, db: Session) -> int:
    """Total badges earned."""
    return db.query(func.count(UserBadge.id)).filter(
        UserBadge.user_id == user_id,
    ).scalar()


def _resolve_gold_spent(user_id: int, db: Session) -> int:
    """Total gold spent (sum of negative CoinLog amounts, returned as positive)."""
    result = db.query(func.coalesce(func.sum(CoinLog.amount), 0)).filter(
        CoinLog.user_id == user_id,
        CoinLog.amount < 0,
    ).scalar()
    return abs(result)


def _resolve_total_gold_earned(user_id: int, db: Session) -> int:
    """Total gold earned (sum of positive CoinLog amounts)."""
    return db.query(func.coalesce(func.sum(CoinLog.amount), 0)).filter(
        CoinLog.user_id == user_id,
        CoinLog.amount > 0,
    ).scalar()


def _resolve_days_employed(user_id: int, db: Session) -> int:
    """Days since start_date."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.start_date:
        return 0
    today = (datetime.utcnow() + timedelta(hours=7)).date()
    return max(0, (today - user.start_date).days)


FIELD_RESOLVERS = {
    "checkin_streak": _resolve_checkin_streak,
    "total_steps": _resolve_total_steps,
    "mana_received": _resolve_mana_received,
    "mana_sent": _resolve_mana_sent,
    "revival_prayers": _resolve_revival_prayers,
    "scroll_purchased": _resolve_scroll_purchased,
    "coins": _resolve_user_field("coins"),
    "angel_coins": _resolve_user_field("angel_coins"),
    "base_str": _resolve_user_field("base_str"),
    "base_def": _resolve_user_field("base_def"),
    "base_luk": _resolve_user_field("base_luk"),
    # Leave counts
    "leave_sick": _resolve_leave("sick"),
    "leave_vacation": _resolve_leave("vacation"),
    "leave_business": _resolve_leave("business"),
    # Total redemptions
    "total_redemptions": _resolve_total_redemptions,
    # Rescue
    "rescue_given": _resolve_rescue_given,
    "rescue_received": _resolve_rescue_received,
    # ── New fields ──
    "total_checkins": _resolve_total_checkins,
    "on_time_checkins": _resolve_on_time_checkins,
    "pvp_wins": _resolve_pvp_wins,
    "pvp_battles": _resolve_pvp_battles,
    "thank_you_sent": _resolve_thank_you_sent,
    "thank_you_received": _resolve_thank_you_received,
    "anonymous_praise_sent": _resolve_anonymous_praise_sent,
    "anonymous_praise_received": _resolve_anonymous_praise_received,
    "fortune_spins": _resolve_fortune_spins,
    "badges_count": _resolve_badges_count,
    "gold_spent": _resolve_gold_spent,
    "total_gold_earned": _resolve_total_gold_earned,
    "days_employed": _resolve_days_employed,
}

# item_<id> fields are registered dynamically — see _ensure_item_fields()

_item_fields_loaded = False

def _ensure_item_fields(db: Session):
    """Lazily load item_<id> fields from the rewards table."""
    global _item_fields_loaded
    if _item_fields_loaded:
        return
    try:
        rewards = db.query(Reward).filter(Reward.is_active == True).all()
        for r in rewards:
            key = f"item_{r.id}"
            if key not in FIELD_RESOLVERS:
                FIELD_RESOLVERS[key] = _resolve_item_purchased(r.id)
                FIELD_DESCRIPTIONS[key] = {
                    "label": f"🛒 {r.name}",
                    "desc": f"Times redeemed \"{r.name}\" (id={r.id})",
                    "example": f"{key} >= 1",
                }
        _item_fields_loaded = True
    except Exception as e:
        logger.error(f"Failed to load item fields: {e}")


FIELD_DESCRIPTIONS = {
    "checkin_streak":     {"label": "Check-in Streak",      "desc": "Consecutive on-time check-in days",        "example": "checkin_streak >= 5"},
    "total_steps":        {"label": "Total Steps",          "desc": "All-time total steps walked (Fitbit)",     "example": "total_steps >= 10000"},
    "mana_received":      {"label": "Mana Received",        "desc": "Times received Mana from others",          "example": "mana_received >= 3"},
    "mana_sent":          {"label": "Mana Sent",            "desc": "Times sent Mana to others",                "example": "mana_sent >= 3"},
    "revival_prayers":    {"label": "🙏 Revival Prayers",   "desc": "Times contributed a Revival Prayer",       "example": "revival_prayers >= 3"},
    "scroll_purchased":   {"label": "📜 Scrolls Purchased", "desc": "Times purchased any Scroll",               "example": "scroll_purchased >= 2"},
    "coins":              {"label": "Gold (current)",       "desc": "Current Gold balance",                     "example": "coins >= 100"},
    "angel_coins":        {"label": "Mana (current)",       "desc": "Current Mana balance",                     "example": "angel_coins >= 10"},
    "base_str":           {"label": "Base STR",             "desc": "Base Strength stat",                       "example": "base_str >= 15"},
    "base_def":           {"label": "Base DEF",             "desc": "Base Defense stat",                        "example": "base_def >= 15"},
    "base_luk":           {"label": "Base LUK",             "desc": "Base Luck stat",                           "example": "base_luk >= 15"},
    "leave_sick":         {"label": "🏥 Sick Leave",        "desc": "Approved sick leave count",                 "example": "leave_sick >= 1"},
    "leave_vacation":     {"label": "🏖 Vacation Leave",    "desc": "Approved vacation leave count",             "example": "leave_vacation >= 1"},
    "leave_business":     {"label": "💼 Business Leave",    "desc": "Approved business leave count",             "example": "leave_business >= 1"},
    "total_redemptions":  {"label": "🛍 Total Redemptions", "desc": "Total items redeemed from shop",            "example": "total_redemptions >= 5"},
    "rescue_given":       {"label": "🆘 Rescue Given",     "desc": "Times contributed a Revival Prayer to help others", "example": "rescue_given >= 3"},
    "rescue_received":    {"label": "💖 Rescue Received",   "desc": "Times successfully revived by friends",          "example": "rescue_received >= 1"},
    # ── New fields ──
    "total_checkins":           {"label": "📋 Total Check-ins",        "desc": "Total number of check-ins",                         "example": "total_checkins >= 30"},
    "on_time_checkins":         {"label": "⏰ On-time Check-ins",      "desc": "Number of on-time check-ins",                       "example": "on_time_checkins >= 20"},
    "pvp_wins":                 {"label": "⚔️ PvP Wins",              "desc": "PvP battles won",                                   "example": "pvp_wins >= 5"},
    "pvp_battles":              {"label": "🏟️ PvP Battles",           "desc": "Total PvP battles played",                          "example": "pvp_battles >= 10"},
    "thank_you_sent":           {"label": "💌 Thank You Sent",         "desc": "Thank You Cards sent",                              "example": "thank_you_sent >= 4"},
    "thank_you_received":       {"label": "💝 Thank You Received",     "desc": "Thank You Cards received",                          "example": "thank_you_received >= 5"},
    "anonymous_praise_sent":    {"label": "🕵️ Praise Sent",           "desc": "Anonymous praises written",                         "example": "anonymous_praise_sent >= 3"},
    "anonymous_praise_received":{"label": "🌟 Praise Received",        "desc": "Anonymous praises received",                        "example": "anonymous_praise_received >= 3"},
    "fortune_spins":            {"label": "🎰 Fortune Spins",          "desc": "Fortune Wheel spins",                               "example": "fortune_spins >= 10"},
    "badges_count":             {"label": "🏅 Badges Count",           "desc": "Total badges earned",                               "example": "badges_count >= 5"},
    "gold_spent":               {"label": "💸 Gold Spent",             "desc": "Total gold spent (all time)",                       "example": "gold_spent >= 100"},
    "total_gold_earned":        {"label": "💰 Gold Earned",            "desc": "Total gold earned (all time)",                      "example": "total_gold_earned >= 500"},
    "days_employed":            {"label": "📅 Days Employed",           "desc": "Days since start date",                             "example": "days_employed >= 365"},
}

# Legacy labels (kept for backward compat)
CONDITION_LABELS = {
    "checkin_streak": "Check-in on time X consecutive days",
    "total_steps": "Walk X total steps",
    "mana_received": "Receive Mana X times",
    "mana_sent": "Send Mana X times",
    "scroll_purchased": "Purchase Scrolls X times",
}


# ── Query Parser ──────────────────────────────────────

OPERATORS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "!=": lambda a, b: a != b,
    "==": lambda a, b: a == b,
    ">":  lambda a, b: a > b,
    "<":  lambda a, b: a < b,
}

# Pattern: field_name  operator  number
CONDITION_RE = re.compile(
    r"(\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+)"
)


def parse_query(query_str: str, db: Session = None):
    """
    Parse a query string into structured conditions.
    Returns: list of (conjunction, field, op_str, value) tuples
    conjunction is 'AND' | 'OR' | None (first condition)

    Example: "total_steps >= 50 AND mana_sent > 3"
    → [(None, 'total_steps', '>=', 50), ('AND', 'mana_sent', '>', 3)]
    """
    if not query_str or not query_str.strip():
        raise ValueError("Query is empty")

    # Load dynamic item fields if db available
    if db:
        _ensure_item_fields(db)

    # Normalize whitespace
    q = query_str.strip()

    # Split by AND/OR (case insensitive), keeping the conjunction
    parts = re.split(r"\s+(AND|OR)\s+", q, flags=re.IGNORECASE)

    conditions = []
    conjunction = None

    for part in parts:
        upper = part.strip().upper()
        if upper in ("AND", "OR"):
            conjunction = upper
            continue

        match = CONDITION_RE.fullmatch(part.strip())
        if not match:
            raise ValueError(f"Invalid condition: '{part.strip()}'. Expected format: field >= value")

        field = match.group(1)
        op_str = match.group(2)
        value = int(match.group(3))

        # Support dynamic item_<id> fields even if not pre-loaded
        if field not in FIELD_RESOLVERS and field.startswith("item_"):
            try:
                reward_id = int(field.split("_", 1)[1])
                FIELD_RESOLVERS[field] = _resolve_item_purchased(reward_id)
            except (ValueError, IndexError):
                pass

        if field not in FIELD_RESOLVERS:
            raise ValueError(f"Unknown field: '{field}'. Available: {', '.join(sorted(FIELD_RESOLVERS.keys()))}")

        conditions.append((conjunction, field, op_str, value))
        conjunction = None  # reset after consuming

    if not conditions:
        raise ValueError("No valid conditions found")

    return conditions


def validate_query(query_str: str, db: Session = None) -> dict:
    """Validate a query string. Returns {valid: bool, error: str|None, fields: list}."""
    try:
        conditions = parse_query(query_str, db)
        fields = [c[1] for c in conditions]
        return {"valid": True, "error": None, "fields": fields, "condition_count": len(conditions)}
    except ValueError as e:
        return {"valid": False, "error": str(e), "fields": [], "condition_count": 0}


def evaluate_query(user_id: int, query_str: str, db: Session) -> bool:
    """Evaluate a query string against a user. Returns True if all conditions are met."""
    conditions = parse_query(query_str, db)

    # Evaluate with AND/OR logic
    result = None
    for conjunction, field, op_str, value in conditions:
        resolver = FIELD_RESOLVERS[field]
        actual = resolver(user_id, db)
        op_fn = OPERATORS[op_str]
        cond_result = op_fn(actual, value)

        if result is None:
            result = cond_result
        elif conjunction == "OR":
            result = result or cond_result
        else:  # AND (default)
            result = result and cond_result

    return bool(result)


def resolve_user_fields(user_id: int, query_str: str, db: Session) -> dict:
    """Resolve all field values mentioned in a query for a given user."""
    conditions = parse_query(query_str, db)
    values = {}
    for _, field, _, _ in conditions:
        if field not in values:
            resolver = FIELD_RESOLVERS[field]
            values[field] = resolver(user_id, db)
    return values

