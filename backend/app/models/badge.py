from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    image = Column(String(500), nullable=True)
    stat_str = Column(Integer, default=0)  # Strength bonus
    stat_def = Column(Integer, default=0)  # Defense bonus
    stat_luk = Column(Integer, default=0)  # Luck bonus
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to user badges
    user_badges = relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan")


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (
        Index("ix_user_badges_user", "user_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    awarded_at = Column(DateTime, default=datetime.utcnow)
    awarded_by = Column(String(200), nullable=True)  # Admin name who awarded

    badge = relationship("Badge", back_populates="user_badges")
    user = relationship("User")

