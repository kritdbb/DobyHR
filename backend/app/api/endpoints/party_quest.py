"""
Party Quest: Admin CRUD + staff progress API.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api import deps
from app.models.user import User, UserRole
from app.models.party_quest import PartyQuest, PartyQuestMember
from app.models.reward import CoinLog
from app.models.badge import Badge, UserBadge

logger = logging.getLogger("hr-api")

router = APIRouter(prefix="/api/party-quest", tags=["Party Quest"])


# ── Schemas ──────────────────────────────────────────────

class MemberIn(BaseModel):
    user_id: int
    team: str  # "A" or "B"

class QuestCreate(BaseModel):
    title: str
    start_date: str  # YYYY-MM-DD
    end_date: str
    team_a_name: str = "Team A"
    team_b_name: str = "Team B"
    members: List[MemberIn]
    steps_goal: Optional[int] = None
    gifts_goal: Optional[int] = None
    battles_goal: Optional[int] = None
    thankyou_goal: Optional[int] = None
    reward_gold: int = 0
    reward_mana: int = 0
    reward_str: int = 0
    reward_def: int = 0
    reward_luk: int = 0
    reward_badge_id: Optional[int] = None

class QuestUpdate(QuestCreate):
    pass


# ── Helpers ──────────────────────────────────────────────

def _now_local():
    return datetime.utcnow() + timedelta(hours=7)


def _compute_progress(db: Session, quest: PartyQuest, team_members_a: list, team_members_b: list):
    """Compute progress for both teams across all active goals."""
    from app.models.social import ThankYouCard
    from app.models.pvp import PvpBattle

    start_utc = datetime.combine(quest.start_date, datetime.min.time()) - timedelta(hours=7)
    end_utc = datetime.combine(quest.end_date, datetime.max.time()) - timedelta(hours=7)
    a_ids = [m.user_id for m in team_members_a]
    b_ids = [m.user_id for m in team_members_b]
    all_ids = a_ids + b_ids

    result = {"team_a": {}, "team_b": {}}

    # Steps
    if quest.steps_goal:
        try:
            from app.models.fitbit import FitbitSteps
            for label, ids in [("team_a", a_ids), ("team_b", b_ids)]:
                total = db.query(func.coalesce(func.sum(FitbitSteps.steps), 0)).filter(
                    FitbitSteps.user_id.in_(ids),
                    FitbitSteps.date >= quest.start_date,
                    FitbitSteps.date <= quest.end_date,
                ).scalar() if ids else 0
                result[label]["steps"] = int(total)
        except Exception:
            result["team_a"]["steps"] = 0
            result["team_b"]["steps"] = 0

    # Gifts received from non-team members
    if quest.gifts_goal:
        from sqlalchemy import or_
        for label, ids, own_ids in [("team_a", a_ids, a_ids), ("team_b", b_ids, b_ids)]:
            total = 0
            if ids:
                total = db.query(func.coalesce(func.sum(CoinLog.amount), 0)).filter(
                    CoinLog.user_id.in_(ids),
                    CoinLog.created_at >= start_utc,
                    CoinLog.created_at <= end_utc,
                    CoinLog.amount > 0,
                    or_(
                        CoinLog.reason.ilike("%Received Angel Coins%"),
                        CoinLog.reason.ilike("%Received Gold from%"),
                        CoinLog.reason.ilike("%Received Mana from%"),
                    ),
                ).scalar()
            result[label]["gifts"] = int(total) if total else 0

    # PvP battles won
    if quest.battles_goal:
        for label, ids in [("team_a", a_ids), ("team_b", b_ids)]:
            count = 0
            if ids:
                count = db.query(func.count(PvpBattle.id)).filter(
                    PvpBattle.winner_id.in_(ids),
                    PvpBattle.status == "resolved",
                    PvpBattle.created_at >= start_utc,
                    PvpBattle.created_at <= end_utc,
                ).scalar()
            result[label]["battles"] = int(count) if count else 0

    # Thank You Cards received
    if quest.thankyou_goal:
        for label, ids in [("team_a", a_ids), ("team_b", b_ids)]:
            count = 0
            if ids:
                count = db.query(func.count(ThankYouCard.id)).filter(
                    ThankYouCard.recipient_id.in_(ids),
                    ThankYouCard.created_at >= start_utc,
                    ThankYouCard.created_at <= end_utc,
                ).scalar()
            result[label]["thankyou"] = int(count) if count else 0

    return result


def _check_and_resolve(db: Session, quest: PartyQuest):
    """Check if any team reached all goals → resolve quest and award rewards."""
    if quest.status != "active" or quest.winner_team:
        return

    members = db.query(PartyQuestMember).filter(PartyQuestMember.quest_id == quest.id).all()
    team_a = [m for m in members if m.team == "A"]
    team_b = [m for m in members if m.team == "B"]

    progress = _compute_progress(db, quest, team_a, team_b)

    goals = {}
    if quest.steps_goal: goals["steps"] = quest.steps_goal
    if quest.gifts_goal: goals["gifts"] = quest.gifts_goal
    if quest.battles_goal: goals["battles"] = quest.battles_goal
    if quest.thankyou_goal: goals["thankyou"] = quest.thankyou_goal

    if not goals:
        return

    a_done = all(progress["team_a"].get(k, 0) >= v for k, v in goals.items())
    b_done = all(progress["team_b"].get(k, 0) >= v for k, v in goals.items())

    winner = None
    if a_done and not b_done:
        winner = "A"
    elif b_done and not a_done:
        winner = "B"
    elif a_done and b_done:
        winner = "A"  # first to reach (both at same check = A wins)

    if not winner:
        # Check if quest expired
        now_date = _now_local().date()
        if now_date > quest.end_date:
            quest.status = "completed"
            db.commit()
        return

    # Award rewards to winning team
    quest.winner_team = winner
    quest.status = "completed"

    winning_members = team_a if winner == "A" else team_b
    team_name = quest.team_a_name if winner == "A" else quest.team_b_name
    team_size = len(winning_members) or 1
    import math
    for m in winning_members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if not user:
            continue

        if quest.reward_gold:
            share = math.ceil(quest.reward_gold / team_size)
            user.coins = (user.coins or 0) + share
            db.add(CoinLog(user_id=user.id, amount=share, reason=f"🤝 Party Quest '{quest.title}' — {team_name} Wins! Gold +{share} (Team Reward {quest.reward_gold}/{team_size})", created_by="System"))
        if quest.reward_mana:
            share = math.ceil(quest.reward_mana / team_size)
            user.angel_coins = (user.angel_coins or 0) + share
            db.add(CoinLog(user_id=user.id, amount=share, reason=f"🤝 Party Quest '{quest.title}' — {team_name} Wins! Mana +{share} (Team Reward {quest.reward_mana}/{team_size})", created_by="System"))
        if quest.reward_str:
            share = math.ceil(quest.reward_str / team_size)
            user.base_str = (user.base_str or 10) + share
        if quest.reward_def:
            share = math.ceil(quest.reward_def / team_size)
            user.base_def = (user.base_def or 10) + share
        if quest.reward_luk:
            share = math.ceil(quest.reward_luk / team_size)
            user.base_luk = (user.base_luk or 10) + share
        if quest.reward_badge_id:
            existing = db.query(UserBadge).filter(UserBadge.user_id == user.id, UserBadge.badge_id == quest.reward_badge_id).first()
            if not existing:
                db.add(UserBadge(user_id=user.id, badge_id=quest.reward_badge_id, awarded_by=f"Party Quest: {quest.title}"))

    db.commit()
    logger.info(f"🤝 Party Quest '{quest.title}' resolved: Team {winner} ({team_name}) wins!")


# ── Admin Endpoints ──────────────────────────────────────

@router.get("")
def list_quests(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """List all party quests (admin)."""
    quests = db.query(PartyQuest).order_by(PartyQuest.created_at.desc()).all()
    result = []
    for q in quests:
        members = db.query(PartyQuestMember).filter(PartyQuestMember.quest_id == q.id).all()
        member_data = []
        for m in members:
            user = db.query(User).filter(User.id == m.user_id).first()
            member_data.append({
                "id": m.id,
                "user_id": m.user_id,
                "team": m.team,
                "name": f"{user.name} {user.surname or ''}".strip() if user else "?",
                "image": user.image if user else None,
            })
        result.append({
            "id": q.id,
            "title": q.title,
            "status": q.status,
            "start_date": q.start_date.isoformat(),
            "end_date": q.end_date.isoformat(),
            "team_a_name": q.team_a_name,
            "team_b_name": q.team_b_name,
            "steps_goal": q.steps_goal,
            "gifts_goal": q.gifts_goal,
            "battles_goal": q.battles_goal,
            "thankyou_goal": q.thankyou_goal,
            "reward_gold": q.reward_gold,
            "reward_mana": q.reward_mana,
            "reward_str": q.reward_str,
            "reward_def": q.reward_def,
            "reward_luk": q.reward_luk,
            "reward_badge_id": q.reward_badge_id,
            "winner_team": q.winner_team,
            "members": member_data,
        })
    return result


@router.post("")
def create_quest(
    data: QuestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Create a new party quest (admin)."""
    from datetime import date as d
    quest = PartyQuest(
        title=data.title,
        start_date=d.fromisoformat(data.start_date),
        end_date=d.fromisoformat(data.end_date),
        team_a_name=data.team_a_name,
        team_b_name=data.team_b_name,
        steps_goal=data.steps_goal if data.steps_goal and data.steps_goal > 0 else None,
        gifts_goal=data.gifts_goal if data.gifts_goal and data.gifts_goal > 0 else None,
        battles_goal=data.battles_goal if data.battles_goal and data.battles_goal > 0 else None,
        thankyou_goal=data.thankyou_goal if data.thankyou_goal and data.thankyou_goal > 0 else None,
        reward_gold=data.reward_gold,
        reward_mana=data.reward_mana,
        reward_str=data.reward_str,
        reward_def=data.reward_def,
        reward_luk=data.reward_luk,
        reward_badge_id=data.reward_badge_id,
    )
    db.add(quest)
    db.commit()
    db.refresh(quest)

    for m in data.members:
        db.add(PartyQuestMember(quest_id=quest.id, user_id=m.user_id, team=m.team))
    db.commit()

    return {"ok": True, "id": quest.id}


@router.put("/{quest_id}")
def update_quest(
    quest_id: int,
    data: QuestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Update an existing party quest (admin)."""
    from datetime import date as d
    quest = db.query(PartyQuest).filter(PartyQuest.id == quest_id).first()
    if not quest:
        raise HTTPException(404, "Quest not found")

    quest.title = data.title
    quest.start_date = d.fromisoformat(data.start_date)
    quest.end_date = d.fromisoformat(data.end_date)
    quest.team_a_name = data.team_a_name
    quest.team_b_name = data.team_b_name
    quest.steps_goal = data.steps_goal if data.steps_goal and data.steps_goal > 0 else None
    quest.gifts_goal = data.gifts_goal if data.gifts_goal and data.gifts_goal > 0 else None
    quest.battles_goal = data.battles_goal if data.battles_goal and data.battles_goal > 0 else None
    quest.thankyou_goal = data.thankyou_goal if data.thankyou_goal and data.thankyou_goal > 0 else None
    quest.reward_gold = data.reward_gold
    quest.reward_mana = data.reward_mana
    quest.reward_str = data.reward_str
    quest.reward_def = data.reward_def
    quest.reward_luk = data.reward_luk
    quest.reward_badge_id = data.reward_badge_id

    # Replace members
    db.query(PartyQuestMember).filter(PartyQuestMember.quest_id == quest_id).delete()
    for m in data.members:
        db.add(PartyQuestMember(quest_id=quest_id, user_id=m.user_id, team=m.team))

    db.commit()
    return {"ok": True}


@router.delete("/{quest_id}")
def delete_quest(
    quest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Delete a party quest (admin)."""
    db.query(PartyQuestMember).filter(PartyQuestMember.quest_id == quest_id).delete()
    db.query(PartyQuest).filter(PartyQuest.id == quest_id).delete()
    db.commit()
    return {"ok": True}


# ── Staff Endpoints ──────────────────────────────────────

@router.get("/active")
def get_active_quest(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get all active and upcoming party quests for staff home."""
    now_date = _now_local().date()

    # Active quests (within date range)
    active_quests = db.query(PartyQuest).filter(
        PartyQuest.status == "active",
        PartyQuest.start_date <= now_date,
        PartyQuest.end_date >= now_date,
    ).order_by(PartyQuest.created_at.desc()).all()

    # Upcoming quests (start_date in the future)
    upcoming_quests = db.query(PartyQuest).filter(
        PartyQuest.status == "active",
        PartyQuest.start_date > now_date,
    ).order_by(PartyQuest.start_date.asc()).all()

    all_quests = [(q, "active") for q in active_quests] + [(q, "upcoming") for q in upcoming_quests]

    if not all_quests:
        return []

    def build_quest_response(quest, quest_state):
        members = db.query(PartyQuestMember).filter(PartyQuestMember.quest_id == quest.id).all()
        team_a = [m for m in members if m.team == "A"]
        team_b = [m for m in members if m.team == "B"]

        progress = {"team_a": {}, "team_b": {}}
        if quest_state == "active":
            _check_and_resolve(db, quest)
            db.refresh(quest)
            progress = _compute_progress(db, quest, team_a, team_b)

        def member_info(m):
            user = db.query(User).filter(User.id == m.user_id).first()
            return {
                "user_id": m.user_id,
                "name": f"{user.name} {user.surname or ''}".strip() if user else "?",
                "image": user.image if user else None,
            }

        goals = []
        if quest.steps_goal:
            goals.append({"type": "steps", "label": "🥾 Steps", "target": quest.steps_goal, "a": progress["team_a"].get("steps", 0), "b": progress["team_b"].get("steps", 0)})
        if quest.gifts_goal:
            goals.append({"type": "gifts", "label": "🎁 Gifts Received", "target": quest.gifts_goal, "a": progress["team_a"].get("gifts", 0), "b": progress["team_b"].get("gifts", 0)})
        if quest.battles_goal:
            goals.append({"type": "battles", "label": "⚔️ PvP Wins", "target": quest.battles_goal, "a": progress["team_a"].get("battles", 0), "b": progress["team_b"].get("battles", 0)})
        if quest.thankyou_goal:
            goals.append({"type": "thankyou", "label": "💌 Thank You Cards", "target": quest.thankyou_goal, "a": progress["team_a"].get("thankyou", 0), "b": progress["team_b"].get("thankyou", 0)})

        rewards = []
        if quest.reward_gold: rewards.append(f"💰Gold {quest.reward_gold}")
        if quest.reward_mana: rewards.append(f"✨Mana {quest.reward_mana}")
        if quest.reward_str: rewards.append(f"⚔️STR+{quest.reward_str}")
        if quest.reward_def: rewards.append(f"🛡️DEF+{quest.reward_def}")
        if quest.reward_luk: rewards.append(f"🍀LUK+{quest.reward_luk}")
        if quest.reward_badge_id:
            badge = db.query(Badge).filter(Badge.id == quest.reward_badge_id).first()
            if badge: rewards.append(f"🏅 {badge.name}")

        return {
            "id": quest.id,
            "title": quest.title,
            "status": quest.status,
            "quest_state": quest_state,
            "start_date": quest.start_date.isoformat(),
            "end_date": quest.end_date.isoformat(),
            "team_a_name": quest.team_a_name,
            "team_b_name": quest.team_b_name,
            "team_a": [member_info(m) for m in team_a],
            "team_b": [member_info(m) for m in team_b],
            "goals": goals,
            "rewards": rewards,
            "winner_team": quest.winner_team,
        }

    return [build_quest_response(q, state) for q, state in all_quests]
