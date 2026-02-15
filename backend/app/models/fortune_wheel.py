from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from app.core.database import Base
from datetime import datetime


class FortuneWheel(Base):
    __tablename__ = "fortune_wheels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    segments = Column(JSON, nullable=False)      # [{label, color, weight, reward_type, reward_amount}]
    spin_min = Column(Integer, default=3)         # min spin strength (full rotations)
    spin_max = Column(Integer, default=7)         # max spin strength (full rotations)
    currency = Column(String(20), default="gold") # "gold" or "mana"
    price = Column(Integer, default=0)            # cost to spin
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
