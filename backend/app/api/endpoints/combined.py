"""
Combined API endpoints to reduce network round-trips.
Instead of 12+ separate API calls, the frontend can use 1 combined call.
These endpoints call existing endpoint functions directly to avoid duplicating logic.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get("/home-data")
def get_home_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Combined endpoint for StaffHome — replaces 12+ API calls with 1."""
    from app.api.endpoints.leaves import get_pending_leave_approvals
    from app.api.endpoints.rewards import get_pending_redemption_approvals
    from app.api.endpoints.work_requests import get_pending_work_requests
    from app.api.endpoints.badges import get_my_badges, get_recent_awards, get_my_stats, get_lucky_wheel_today
    from app.api.endpoints.party_quest import get_active_quest
    from app.api.endpoints.social import get_reactions
    from app.api.endpoints.users import get_negative_coin_users, get_rescue_pool
    from app.api.endpoints.pvp import get_today_battles
    from app.models.reward import CoinLog
    from sqlalchemy import desc

    user_id = current_user.id

    # ─── User info ───
    user_data = {
        "id": current_user.id,
        "name": current_user.name,
        "surname": current_user.surname or "",
        "email": current_user.email,
        "position": current_user.position,
        "department": current_user.department,
        "role": current_user.role.value if current_user.role else "staff",
        "coins": current_user.coins or 0,
        "angel_coins": current_user.angel_coins or 0,
        "image": current_user.image,
        "status_text": current_user.status_text or "",
        "circle_artifact": current_user.circle_artifact or "",
        "magic_background": current_user.magic_background or "",
    }

    # ─── Coin logs ───
    coin_logs_raw = (
        db.query(CoinLog)
        .filter(CoinLog.user_id == user_id)
        .order_by(desc(CoinLog.created_at))
        .limit(50)
        .all()
    )
    coin_logs = [{
        "id": cl.id, "amount": cl.amount, "reason": cl.reason or "",
        "log_type": cl.log_type or "",
        "created_at": cl.created_at.isoformat() if cl.created_at else None,
    } for cl in coin_logs_raw]

    # ─── Call existing endpoint functions ───
    try:
        pending_leaves = get_pending_leave_approvals(db=db, current_user=current_user)
    except Exception:
        pending_leaves = []

    try:
        pending_redemptions = get_pending_redemption_approvals(db=db, current_user=current_user)
    except Exception:
        pending_redemptions = []

    try:
        pending_work = get_pending_work_requests(db=db, current_user=current_user)
    except Exception:
        pending_work = []

    try:
        my_badges = get_my_badges(db=db, current_user=current_user)
    except Exception:
        my_badges = []

    try:
        recent_awards = get_recent_awards(limit=50, db=db, current_user=current_user)
    except Exception:
        recent_awards = []

    try:
        my_stats = get_my_stats(db=db, current_user=current_user)
    except Exception:
        my_stats = {}

    try:
        party_quests = get_active_quest(db=db, current_user=current_user)
    except Exception:
        party_quests = []

    try:
        arena_battles = get_today_battles(db=db, current_user=current_user)
    except Exception:
        arena_battles = []

    try:
        lucky_wheel = get_lucky_wheel_today(db=db, current_user=current_user)
    except Exception:
        lucky_wheel = None

    # ─── Reactions (needs award event IDs) ───
    reactions = {}
    try:
        if recent_awards:
            event_ids_str = ",".join(str(a.get("id", a.id if hasattr(a, "id") else "")) for a in recent_awards if a)
            if event_ids_str:
                reactions = get_reactions(event_ids=event_ids_str, db=db, current_user=current_user)
    except Exception:
        pass

    # ─── Negative users + rescue pools ───
    negative_users = []
    try:
        neg_raw = get_negative_coin_users(db=db, current_user=current_user)
        for nu in neg_raw:
            uid = nu.get("id", nu.id if hasattr(nu, "id") else None)
            if uid:
                try:
                    pool = get_rescue_pool(user_id=uid, db=db, current_user=current_user)
                    nu_dict = dict(nu) if isinstance(nu, dict) else {"id": uid, "name": getattr(nu, "name", ""), "coins": getattr(nu, "coins", 0)}
                    nu_dict["pool"] = pool
                    negative_users.append(nu_dict)
                except Exception:
                    nu_dict = dict(nu) if isinstance(nu, dict) else {"id": uid}
                    nu_dict["pool"] = None
                    negative_users.append(nu_dict)
    except Exception:
        pass

    return {
        "user": user_data,
        "coin_logs": coin_logs,
        "pending_leaves": pending_leaves,
        "pending_redemptions": pending_redemptions,
        "pending_work_requests": pending_work,
        "my_badges": my_badges,
        "my_stats": my_stats,
        "recent_awards": recent_awards,
        "reactions": reactions,
        "party_quests": party_quests,
        "negative_users": negative_users,
        "arena_battles": arena_battles,
        "lucky_wheel": lucky_wheel,
    }


@router.get("/services-data")
def get_services_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Combined endpoint for StaffServices — replaces 4 API calls with 1."""
    from app.models.leave import LeaveRequest
    from app.models.reward import Redemption
    from app.models.approval import ApprovalFlow

    user_id = current_user.id

    my_leaves = db.query(LeaveRequest).filter(LeaveRequest.user_id == user_id, LeaveRequest.status == "pending").count()

    pending_leave_approvals = (
        db.query(ApprovalFlow).filter(
            ApprovalFlow.approver_id == user_id,
            ApprovalFlow.status == "pending",
            ApprovalFlow.entity_type == "leave",
        ).count()
    )
    pending_redeem_approvals = (
        db.query(ApprovalFlow).filter(
            ApprovalFlow.approver_id == user_id,
            ApprovalFlow.status == "pending",
            ApprovalFlow.entity_type == "redemption",
        ).count()
    )

    my_coupons = (
        db.query(Redemption).filter(
            Redemption.user_id == user_id,
            Redemption.status.in_(["ready", "approved", "pending"]),
        ).count()
    )

    return {
        "badges": {
            "leave": my_leaves,
            "approvals": pending_leave_approvals + pending_redeem_approvals,
            "coupons": my_coupons,
        }
    }
