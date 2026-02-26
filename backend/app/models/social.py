"""
Social features: Thank You Cards, Anonymous Praise, Town Crier Reactions, Stat Buffs.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.core.database import Base


class ThankYouCard(Base):
    __tablename__ = "thank_you_cards"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_key = Column(String(10), nullable=False)  # e.g. "2026-W08"
    created_at = Column(DateTime, default=datetime.utcnow)


class AnonymousPraise(Base):
    __tablename__ = "anonymous_praises"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    date_key = Column(String(10), nullable=False)  # e.g. "2026-02-17"
    created_at = Column(DateTime, default=datetime.utcnow)


class TownCrierReaction(Base):
    __tablename__ = "town_crier_reactions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), nullable=False, index=True)  # e.g. "badge-42", "mana-123"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emoji = Column(String(10), nullable=False)  # e.g. "❤️", "👏", "🎉"
    created_at = Column(DateTime, default=datetime.utcnow)


class StatBuff(Base):
    __tablename__ = "stat_buffs"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stat_type = Column(String(3), nullable=False)  # "str", "def", "luk"
    amount = Column(Integer, default=1)
    date_key = Column(String(10), nullable=False)  # YYYY-MM-DD, expires at midnight
    created_at = Column(DateTime, default=datetime.utcnow)

