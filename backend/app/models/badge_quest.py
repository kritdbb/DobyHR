from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class BadgeQuest(Base):
    __tablename__ = "badge_quests"

    id = Column(Integer, primary_key=True, index=True)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    condition_type = Column(String(50), nullable=True)  # legacy: checkin_streak, total_steps
    threshold = Column(Integer, nullable=True, default=1)  # legacy threshold
    condition_query = Column(Text, nullable=True)  # new: "total_steps >= 50 AND mana_sent > 3"
    is_active = Column(Boolean, default=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    badge = relationship("Badge")
