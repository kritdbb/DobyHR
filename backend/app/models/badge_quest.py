from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class BadgeQuest(Base):
    __tablename__ = "badge_quests"

    id = Column(Integer, primary_key=True, index=True)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=True)   # nullable: rewards can be non-badge
    condition_type = Column(String(50), nullable=True)  # legacy: checkin_streak, total_steps
    threshold = Column(Integer, nullable=True, default=1)  # legacy threshold
    condition_query = Column(Text, nullable=True)  # new: "total_steps >= 50 AND mana_sent > 3"
    is_active = Column(Boolean, default=True)
    max_awards = Column(Integer, nullable=True, default=None)  # None = unlimited
    description = Column(String(500), nullable=True)
    # Reward system: type = badge (default) / gold / mana / str / def / luk / coupon
    reward_type = Column(String(20), nullable=True, default="badge")
    reward_value = Column(Integer, nullable=True, default=0)  # amount for gold/mana/stat, reward_id for coupon
    created_at = Column(DateTime, default=datetime.utcnow)

    badge = relationship("Badge")
