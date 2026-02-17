"""
Social features: Thank You Cards & Anonymous Praise.
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
