from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, JSON
from datetime import datetime
from app.core.database import Base


class PvpBattle(Base):
    __tablename__ = "pvp_battles"

    id = Column(Integer, primary_key=True, index=True)
    battle_date = Column(Date, nullable=False, index=True)
    scheduled_time = Column(DateTime, nullable=True)  # Admin-set battle time

    player_a_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_b_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Snapshot stats at match time (for replay accuracy)
    a_str = Column(Integer, default=0)
    a_def = Column(Integer, default=0)
    a_luk = Column(Integer, default=0)
    b_str = Column(Integer, default=0)
    b_def = Column(Integer, default=0)
    b_luk = Column(Integer, default=0)

    # Winner rewards
    winner_gold = Column(Integer, default=0)
    winner_mana = Column(Integer, default=0)
    winner_str = Column(Integer, default=0)
    winner_def = Column(Integer, default=0)
    winner_luk = Column(Integer, default=0)

    # Loser penalties (positive numbers = amount to lose)
    loser_gold = Column(Integer, default=0)
    loser_mana = Column(Integer, default=0)
    loser_str = Column(Integer, default=0)
    loser_def = Column(Integer, default=0)
    loser_luk = Column(Integer, default=0)

    # Results
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    loser_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    battle_log = Column(JSON, nullable=True)  # Turn-by-turn events for replay
    gold_stolen = Column(Integer, default=0)  # Legacy / actual gold transferred

    status = Column(String(20), default="scheduled")  # scheduled | resolved

    created_at = Column(DateTime, default=datetime.utcnow)
