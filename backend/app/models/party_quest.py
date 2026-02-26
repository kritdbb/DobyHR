"""
Party Quest: team-based competition system.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, JSON
from app.core.database import Base


class PartyQuest(Base):
    __tablename__ = "party_quests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    status = Column(String(20), default="active")  # active | completed | cancelled

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    team_a_name = Column(String(100), default="Team A")
    team_b_name = Column(String(100), default="Team B")

    # Goals (null/0 = not used in this quest)
    steps_goal = Column(Integer, nullable=True)       # Total team steps
    gifts_goal = Column(Integer, nullable=True)        # Total gifts received from non-team
    battles_goal = Column(Integer, nullable=True)      # Total PvP wins
    thankyou_goal = Column(Integer, nullable=True)     # Total Thank You Cards received

    # Rewards for winning team (each member gets these)
    reward_gold = Column(Integer, default=0)
    reward_mana = Column(Integer, default=0)
    reward_str = Column(Integer, default=0)
    reward_def = Column(Integer, default=0)
    reward_luk = Column(Integer, default=0)
    reward_badge_id = Column(Integer, ForeignKey("badges.id"), nullable=True)

    winner_team = Column(String(1), nullable=True)  # "A" or "B" or null

    created_at = Column(DateTime, default=datetime.utcnow)


class PartyQuestMember(Base):
    __tablename__ = "party_quest_members"

    id = Column(Integer, primary_key=True, index=True)
    quest_id = Column(Integer, ForeignKey("party_quests.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team = Column(String(1), nullable=False)  # "A" or "B"
