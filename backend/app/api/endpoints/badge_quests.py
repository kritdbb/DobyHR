"""
Badge Quest CRUD + evaluation endpoints.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.badge import Badge, UserBadge
from app.models.badge_quest import BadgeQuest
from app.api import deps
from app.services.badge_quest_evaluator import (
    CONDITION_LABELS, FIELD_DESCRIPTIONS, FIELD_RESOLVERS,
    evaluate_query, validate_query,
    resolve_user_fields,
)

logger = logging.getLogger("hr-api")

router = APIRouter(prefix="/api/badge-quests", tags=["Badge Quests"])


# ── Schemas ───────────────────────────────────────────

class BadgeQuestCreate(BaseModel):
    badge_id: Optional[int] = None                 # optional: only needed for badge rewards
    condition_query: Optional[str] = None          # new query style
    condition_type: Optional[str] = None           # legacy
    threshold: Optional[int] = None                # legacy
    is_active: bool = True
    description: Optional[str] = None
    max_awards: Optional[int] = None               # None = unlimited
    reward_type: Optional[str] = "badge"           # badge/gold/mana/str/def/luk/coupon
    reward_value: Optional[int] = 0                # amount or item id


class BadgeQuestUpdate(BaseModel):
    badge_id: Optional[int] = None
    condition_query: Optional[str] = None
    condition_type: Optional[str] = None
    threshold: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    max_awards: Optional[int] = None               # None = unlimited, 0 to clear
    reward_type: Optional[str] = None
    reward_value: Optional[int] = None


# ── Fields & Condition Types ─────────────────────────

@router.get("/condition-types")
def get_condition_types(
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Return available condition types with labels (legacy)."""
    return [
        {"key": k, "label": v}
        for k, v in CONDITION_LABELS.items()
    ]


@router.get("/fields")
def get_available_fields(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Return all queryable fields with descriptions and examples."""
    from app.services.badge_quest_evaluator import _ensure_item_fields
    _ensure_item_fields(db)
    return [
        {"field": k, **v}
        for k, v in FIELD_DESCRIPTIONS.items()
    ]


# ── CRUD ──────────────────────────────────────────────

@router.get("/")
def list_quests(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """List all badge quests with badge details."""
    quests = db.query(BadgeQuest).order_by(BadgeQuest.id.desc()).all()
    result = []
    for q in quests:
        badge = db.query(Badge).filter(Badge.id == q.badge_id).first() if q.badge_id else None
        # Count current holders for this badge
        from sqlalchemy import func
        current_awards = 0
        if q.badge_id:
            current_awards = db.query(func.count(UserBadge.id)).filter(
                UserBadge.badge_id == q.badge_id
            ).scalar() or 0
        result.append({
            "id": q.id,
            "badge_id": q.badge_id,
            "badge_name": badge.name if badge else None,
            "badge_image": badge.image if badge else None,
            "condition_query": q.condition_query,
            "condition_type": q.condition_type,
            "condition_label": CONDITION_LABELS.get(q.condition_type, q.condition_type) if q.condition_type else None,
            "threshold": q.threshold,
            "is_active": q.is_active,
            "max_awards": q.max_awards,
            "current_awards": current_awards,
            "description": q.description,
            "reward_type": q.reward_type or "badge",
            "reward_value": q.reward_value or 0,
            "created_at": q.created_at.isoformat() if q.created_at else None,
        })
    return result


VALID_REWARD_TYPES = ["badge", "gold", "mana", "str", "def", "luk", "coupon"]


@router.post("/")
def create_quest(
    body: BadgeQuestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Create a new badge quest."""
    reward_type = body.reward_type or "badge"
    if reward_type not in VALID_REWARD_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid reward_type. Must be one of: {VALID_REWARD_TYPES}")

    # Validate badge_id only if reward_type is badge
    if reward_type == "badge":
        if not body.badge_id:
            raise HTTPException(status_code=400, detail="badge_id is required for badge rewards")
        badge = db.query(Badge).filter(Badge.id == body.badge_id).first()
        if not badge:
            raise HTTPException(status_code=404, detail="Badge not found")

    # Validate: must have either condition_query or condition_type
    if body.condition_query:
        v = validate_query(body.condition_query, db)
        if not v["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid query: {v['error']}")
    elif body.condition_type:
        if body.condition_type not in CONDITION_LABELS:
            raise HTTPException(status_code=400, detail=f"Invalid condition_type")
        if not body.threshold or body.threshold < 1:
            raise HTTPException(status_code=400, detail="Threshold must be >= 1")
    else:
        raise HTTPException(status_code=400, detail="Must provide condition_query or condition_type")

    quest = BadgeQuest(
        badge_id=body.badge_id if reward_type == "badge" else None,
        condition_query=body.condition_query,
        condition_type=body.condition_type if not body.condition_query else None,
        threshold=body.threshold if not body.condition_query else None,
        is_active=body.is_active,
        description=body.description,
        max_awards=body.max_awards,
        reward_type=reward_type,
        reward_value=body.reward_value or 0,
    )
    db.add(quest)
    db.commit()
    db.refresh(quest)
    return {"id": quest.id, "message": "Quest created"}


@router.put("/{quest_id}")
def update_quest(
    quest_id: int,
    body: BadgeQuestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Update an existing badge quest."""
    quest = db.query(BadgeQuest).filter(BadgeQuest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    if body.badge_id is not None:
        badge = db.query(Badge).filter(Badge.id == body.badge_id).first()
        if not badge:
            raise HTTPException(status_code=404, detail="Badge not found")
        quest.badge_id = body.badge_id

    if body.condition_query is not None:
        if body.condition_query:
            v = validate_query(body.condition_query, db)
            if not v["valid"]:
                raise HTTPException(status_code=400, detail=f"Invalid query: {v['error']}")
            quest.condition_query = body.condition_query
            quest.condition_type = None  # switch to query mode
            quest.threshold = None
        else:
            quest.condition_query = None

    if body.condition_type is not None:
        if body.condition_type not in CONDITION_LABELS:
            raise HTTPException(status_code=400, detail="Invalid condition_type")
        quest.condition_type = body.condition_type
    if body.threshold is not None:
        quest.threshold = body.threshold
    if body.is_active is not None:
        quest.is_active = body.is_active
    if body.description is not None:
        quest.description = body.description
    if body.max_awards is not None:
        quest.max_awards = body.max_awards if body.max_awards > 0 else None
    if body.reward_type is not None:
        if body.reward_type not in VALID_REWARD_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid reward_type")
        quest.reward_type = body.reward_type
        # Clear badge_id if switching to non-badge reward
        if body.reward_type != "badge":
            quest.badge_id = None
    if body.reward_value is not None:
        quest.reward_value = body.reward_value

    db.commit()
    return {"message": "Quest updated"}


@router.delete("/{quest_id}")
def delete_quest(
    quest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Delete a badge quest."""
    quest = db.query(BadgeQuest).filter(BadgeQuest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    db.delete(quest)
    db.commit()
    return {"message": "Quest deleted"}


# ── Preview ───────────────────────────────────────────

class PreviewRequest(BaseModel):
    query: str


@router.post("/preview")
def preview_query(
    body: PreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Dry-run a query: returns matching users without awarding anything."""
    v = validate_query(body.query, db)
    if not v["valid"]:
        raise HTTPException(status_code=400, detail=f"Invalid query: {v['error']}")

    users = db.query(User).all()
    matches = []
    for user in users:
        try:
            if evaluate_query(user.id, body.query, db):
                user_name = f"{user.name} {user.surname or ''}".strip()
                values = resolve_user_fields(user.id, body.query, db)
                matches.append({
                    "user_id": user.id,
                    "user_name": user_name,
                    "user_image": user.image,
                    "field_values": values,
                })
        except Exception as e:
            logger.error(f"Preview error for user {user.id}: {e}")

    return {
        "query": body.query,
        "total_users": len(users),
        "matching_users": len(matches),
        "users": matches,
        "validation": v,
    }


# ── Evaluation ────────────────────────────────────────

@router.post("/evaluate")
def evaluate_all_quests(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Manually trigger evaluation for all active quests × all users."""
    return _run_evaluation(db)


def _run_evaluation(db: Session):
    """Core evaluation logic, used by both API and scheduler."""
    from app.models.reward import CoinLog, Redemption
    active_quests = db.query(BadgeQuest).filter(BadgeQuest.is_active == True).all()
    logger.info(f"🎯 Badge Quest eval: {len(active_quests)} active quest(s)")
    if not active_quests:
        return {"awarded": 0, "details": []}

    users = db.query(User).all()
    logger.info(f"🎯 Evaluating {len(users)} user(s)")
    awarded_list = []

    for quest in active_quests:
        reward_type = quest.reward_type or "badge"
        reward_value = quest.reward_value or 0

        # For badge type, badge must exist
        badge = None
        if reward_type == "badge":
            badge = db.query(Badge).filter(Badge.id == quest.badge_id).first()
            if not badge:
                continue

        for user in users:
            # Skip if already awarded
            if reward_type == "badge":
                existing = db.query(UserBadge).filter(
                    UserBadge.user_id == user.id,
                    UserBadge.badge_id == quest.badge_id,
                ).first()
                if existing:
                    continue
            else:
                # For non-badge rewards, check CoinLog for quest award marker
                existing = db.query(CoinLog).filter(
                    CoinLog.user_id == user.id,
                    CoinLog.reason == f"🎯 Quest #{quest.id} reward",
                ).first()
                if existing:
                    continue

            # Evaluate: prefer query, fallback to legacy (auto-convert to query)
            met = False
            effective_query = quest.condition_query
            if not effective_query and quest.condition_type:
                effective_query = f"{quest.condition_type} >= {quest.threshold or 1}"
            if effective_query:
                try:
                    met = evaluate_query(user.id, effective_query, db)
                except Exception as e:
                    logger.error(f"Query eval error quest={quest.id} user={user.id}: {e}")

            user_name = f"{user.name} {user.surname or ''}".strip()
            query_display = effective_query or "(no condition)"

            if met:
                # Check max_awards limit
                if quest.max_awards is not None:
                    from sqlalchemy import func as sqlfunc
                    if reward_type == "badge":
                        count = db.query(sqlfunc.count(UserBadge.id)).filter(
                            UserBadge.badge_id == quest.badge_id
                        ).scalar() or 0
                    else:
                        count = db.query(sqlfunc.count(CoinLog.id)).filter(
                            CoinLog.reason == f"🎯 Quest #{quest.id} reward",
                        ).scalar() or 0
                    if count >= quest.max_awards:
                        quest.is_active = False
                        logger.info(f"🔒 Quest {quest.id} auto-disabled: limit reached")
                        break

                # Grant reward
                reward_label = ""
                if reward_type == "badge":
                    ub = UserBadge(user_id=user.id, badge_id=quest.badge_id, awarded_by="Badge Quest")
                    db.add(ub)
                    reward_label = f"Badge: {badge.name}"
                elif reward_type == "gold":
                    user.coins = (user.coins or 0) + reward_value
                    db.add(CoinLog(user_id=user.id, amount=reward_value, reason=f"🎯 Quest #{quest.id} reward", created_by="Badge Quest"))
                    reward_label = f"+{reward_value} Gold"
                elif reward_type == "mana":
                    user.angel_coins = (user.angel_coins or 0) + reward_value
                    db.add(CoinLog(user_id=user.id, amount=0, reason=f"🎯 Quest #{quest.id} reward", created_by="Badge Quest"))
                    reward_label = f"+{reward_value} Mana"
                elif reward_type == "str":
                    user.base_str = (user.base_str or 0) + reward_value
                    db.add(CoinLog(user_id=user.id, amount=0, reason=f"🎯 Quest #{quest.id} reward", created_by="Badge Quest"))
                    reward_label = f"+{reward_value} STR"
                elif reward_type == "def":
                    user.base_def = (user.base_def or 0) + reward_value
                    db.add(CoinLog(user_id=user.id, amount=0, reason=f"🎯 Quest #{quest.id} reward", created_by="Badge Quest"))
                    reward_label = f"+{reward_value} DEF"
                elif reward_type == "luk":
                    user.base_luk = (user.base_luk or 0) + reward_value
                    db.add(CoinLog(user_id=user.id, amount=0, reason=f"🎯 Quest #{quest.id} reward", created_by="Badge Quest"))
                    reward_label = f"+{reward_value} LUK"
                elif reward_type == "coupon":
                    from app.models.reward import Reward
                    reward_item = db.query(Reward).filter(Reward.id == reward_value).first()
                    if reward_item:
                        redemption = Redemption(user_id=user.id, reward_id=reward_value, status="approved")
                        db.add(redemption)
                        db.add(CoinLog(user_id=user.id, amount=0, reason=f"🎯 Quest #{quest.id} reward", created_by="Badge Quest"))
                        reward_label = f"Coupon: {reward_item.name}"
                    else:
                        reward_label = f"Coupon (item {reward_value} not found)"

                db.flush()
                awarded_list.append({
                    "user_id": user.id,
                    "user_name": user_name,
                    "reward": reward_label,
                    "query": query_display,
                })
                logger.info(f"🏅 Quest #{quest.id} → {user_name}: {reward_label}")

    db.commit()
    return {"awarded": len(awarded_list), "details": awarded_list}


# ── Staff: My Progress ───────────────────────────────

@router.get("/my-progress")
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get current user's progress toward each active badge quest."""
    from app.models.reward import CoinLog
    active_quests = db.query(BadgeQuest).filter(BadgeQuest.is_active == True).all()
    result = []
    for quest in active_quests:
        reward_type = quest.reward_type or "badge"
        badge = None
        if quest.badge_id:
            badge = db.query(Badge).filter(Badge.id == quest.badge_id).first()

        # Check if already awarded
        completed = False
        if reward_type == "badge" and quest.badge_id:
            existing = db.query(UserBadge).filter(
                UserBadge.user_id == current_user.id,
                UserBadge.badge_id == quest.badge_id,
            ).first()
            completed = existing is not None
        else:
            existing = db.query(CoinLog).filter(
                CoinLog.user_id == current_user.id,
                CoinLog.reason == f"🎯 Quest #{quest.id} reward",
            ).first()
            completed = existing is not None

        # Get progress
        effective_query = quest.condition_query
        if not effective_query and quest.condition_type:
            effective_query = f"{quest.condition_type} >= {quest.threshold or 1}"
        if effective_query:
            progress_data = resolve_user_fields(current_user.id, effective_query, db)
        else:
            progress_data = {}

        result.append({
            "quest_id": quest.id,
            "badge_id": quest.badge_id,
            "badge_name": badge.name if badge else None,
            "badge_image": badge.image if badge else None,
            "condition_query": quest.condition_query,
            "condition_type": quest.condition_type,
            "condition_label": CONDITION_LABELS.get(quest.condition_type, quest.condition_type) if quest.condition_type else None,
            "threshold": quest.threshold,
            "progress": progress_data,
            "completed": completed,
            "description": quest.description,
            "reward_type": reward_type,
            "reward_value": quest.reward_value or 0,
        })
    return result


# ── Push to Production ────────────────────────────────

@router.post("/{quest_id}/push-to-prod")
def push_quest_to_prod(
    quest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Push a badge quest from this server to production via sync API."""
    import httpx
    from app.core.config import settings

    quest = db.query(BadgeQuest).filter(BadgeQuest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    prod_url = settings.PROD_API_URL.rstrip("/")
    sync_key = settings.PROD_SYNC_KEY
    if not sync_key:
        raise HTTPException(status_code=503, detail="PROD_SYNC_KEY not configured")

    # Resolve badge name for the quest
    badge_name = None
    if quest.badge_id:
        badge = db.query(Badge).filter(Badge.id == quest.badge_id).first()
        if badge:
            badge_name = badge.name

    payload = {
        "badge_name": badge_name,
        "condition_query": quest.condition_query,
        "condition_type": quest.condition_type,
        "threshold": quest.threshold,
        "is_active": quest.is_active,
        "description": quest.description,
        "max_awards": quest.max_awards,
        "reward_type": quest.reward_type or "badge",
        "reward_value": quest.reward_value or 0,
    }

    try:
        resp = httpx.post(
            f"{prod_url}/api/sync/badge-quest",
            json=payload,
            headers={"X-Sync-Key": sync_key, "Content-Type": "application/json"},
            timeout=30,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Prod returned {resp.status_code}: {resp.text}")
        return {"message": "Quest pushed to production", "prod_response": resp.json()}
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to connect to prod: {e}")

