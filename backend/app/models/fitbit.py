from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class FitbitToken(Base):
    __tablename__ = "fitbit_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    access_token = Column(String(1000), nullable=False)
    refresh_token = Column(String(1000), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    fitbit_user_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="fitbit_token")


class FitbitSteps(Base):
    __tablename__ = "fitbit_steps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    steps = Column(Integer, default=0)
    synced_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="fitbit_steps")

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_date_steps"),
    )
