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
    evaluate_user, evaluate_query, validate_query,
    get_user_progress, resolve_user_fields,
)

logger = logging.getLogger("hr-api")

router = APIRouter(prefix="/api/badge-quests", tags=["Badge Quests"])


# ── Schemas ───────────────────────────────────────────

class BadgeQuestCreate(BaseModel):
    badge_id: int
    condition_query: Optional[str] = None          # new query style
    condition_type: Optional[str] = None           # legacy
    threshold: Optional[int] = None                # legacy
    is_active: bool = True
    description: Optional[str] = None
    max_awards: Optional[int] = None               # None = unlimited


class BadgeQuestUpdate(BaseModel):
    badge_id: Optional[int] = None
    condition_query: Optional[str] = None
    condition_type: Optional[str] = None
    threshold: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    max_awards: Optional[int] = None               # None = unlimited, 0 to clear


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
        badge = db.query(Badge).filter(Badge.id == q.badge_id).first()
        # Count current holders for this badge
        from sqlalchemy import func
        current_awards = db.query(func.count(UserBadge.id)).filter(
            UserBadge.badge_id == q.badge_id
        ).scalar() or 0
        result.append({
            "id": q.id,
            "badge_id": q.badge_id,
            "badge_name": badge.name if badge else "—",
            "badge_image": badge.image if badge else None,
            "condition_query": q.condition_query,
            "condition_type": q.condition_type,
            "condition_label": CONDITION_LABELS.get(q.condition_type, q.condition_type) if q.condition_type else None,
            "threshold": q.threshold,
            "is_active": q.is_active,
            "max_awards": q.max_awards,
            "current_awards": current_awards,
            "description": q.description,
            "created_at": q.created_at.isoformat() if q.created_at else None,
        })
    return result


@router.post("/")
def create_quest(
    body: BadgeQuestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_gm_or_above),
):
    """Create a new badge quest."""
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
        badge_id=body.badge_id,
        condition_query=body.condition_query,
        condition_type=body.condition_type if not body.condition_query else None,
        threshold=body.threshold if not body.condition_query else None,
        is_active=body.is_active,
        description=body.description,
        max_awards=body.max_awards,
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
    active_quests = db.query(BadgeQuest).filter(BadgeQuest.is_active == True).all()
    logger.info(f"🎯 Badge Quest eval: {len(active_quests)} active quest(s)")
    if not active_quests:
        return {"awarded": 0, "details": []}

    users = db.query(User).all()
    logger.info(f"🎯 Evaluating {len(users)} user(s)")
    awarded_list = []

    for quest in active_quests:
        badge = db.query(Badge).filter(Badge.id == quest.badge_id).first()
        if not badge:
            continue

        for user in users:
            # Skip if user already has this badge
            existing = db.query(UserBadge).filter(
                UserBadge.user_id == user.id,
                UserBadge.badge_id == quest.badge_id,
            ).first()
            if existing:
                continue

            # Evaluate: prefer query, fallback to legacy
            met = False
            if quest.condition_query:
                try:
                    met = evaluate_query(user.id, quest.condition_query, db)
                except Exception as e:
                    logger.error(f"Query eval error quest={quest.id} user={user.id}: {e}")
            elif quest.condition_type:
                met = evaluate_user(user.id, quest.condition_type, quest.threshold or 1, db)

            user_name = f"{user.name} {user.surname or ''}".strip()
            query_display = quest.condition_query or f"{quest.condition_type} >= {quest.threshold}"
            logger.info(f"🎯 {user_name}: [{query_display}] → {'✅' if met else '❌'}")

            if met:
                # Check max_awards limit before awarding
                if quest.max_awards is not None:
                    from sqlalchemy import func as sqlfunc
                    holder_count = db.query(sqlfunc.count(UserBadge.id)).filter(
                        UserBadge.badge_id == quest.badge_id
                    ).scalar() or 0
                    if holder_count >= quest.max_awards:
                        # Limit reached — auto-disable this quest
                        quest.is_active = False
                        logger.info(f"🔒 Quest {quest.id} auto-disabled: {holder_count}/{quest.max_awards} reached")
                        break  # stop processing more users for this quest

                ub = UserBadge(
                    user_id=user.id,
                    badge_id=quest.badge_id,
                    awarded_by="Badge Quest",
                )
                db.add(ub)
                db.flush()  # flush so holder_count is accurate for next iteration
                awarded_list.append({
                    "user_id": user.id,
                    "user_name": user_name,
                    "badge_name": badge.name,
                    "query": query_display,
                })
                logger.info(f"🏅 Badge Quest awarded '{badge.name}' to {user_name}")

                # Re-check limit after awarding
                if quest.max_awards is not None:
                    from sqlalchemy import func as sqlfunc
                    holder_count = db.query(sqlfunc.count(UserBadge.id)).filter(
                        UserBadge.badge_id == quest.badge_id
                    ).scalar() or 0
                    if holder_count >= quest.max_awards:
                        quest.is_active = False
                        logger.info(f"🔒 Quest {quest.id} auto-disabled: {holder_count}/{quest.max_awards} reached")
                        break

    db.commit()
    return {"awarded": len(awarded_list), "details": awarded_list}


# ── Staff: My Progress ───────────────────────────────

@router.get("/my-progress")
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get current user's progress toward each active badge quest."""
    active_quests = db.query(BadgeQuest).filter(BadgeQuest.is_active == True).all()
    result = []
    for quest in active_quests:
        badge = db.query(Badge).filter(Badge.id == quest.badge_id).first()
        if not badge:
            continue

        # Check if already awarded
        existing = db.query(UserBadge).filter(
            UserBadge.user_id == current_user.id,
            UserBadge.badge_id == quest.badge_id,
        ).first()

        # Get progress
        if quest.condition_query:
            progress_data = resolve_user_fields(current_user.id, quest.condition_query, db)
        else:
            progress_val = get_user_progress(current_user.id, quest.condition_type, db) if quest.condition_type else 0
            progress_data = {quest.condition_type: progress_val} if quest.condition_type else {}

        result.append({
            "quest_id": quest.id,
            "badge_id": quest.badge_id,
            "badge_name": badge.name,
            "badge_image": badge.image,
            "condition_query": quest.condition_query,
            "condition_type": quest.condition_type,
            "condition_label": CONDITION_LABELS.get(quest.condition_type, quest.condition_type) if quest.condition_type else None,
            "threshold": quest.threshold,
            "progress": progress_data,
            "completed": existing is not None,
            "description": quest.description,
        })
    return result
