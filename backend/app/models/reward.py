from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum as SAEnum, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class RedemptionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"   # internal approval step
    READY = "ready"         # Approved by workflow, ready to handover
    COMPLETED = "completed" # Handed over
    REJECTED = "rejected"

class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    image = Column(String(500), nullable=True)
    point_cost = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

class Redemption(Base):
    __tablename__ = "redemptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_id = Column(Integer, ForeignKey("rewards.id"), nullable=False)
    status = Column(SAEnum(RedemptionStatus), default=RedemptionStatus.PENDING)
    qr_code = Column(String(100), unique=True, index=True, nullable=True) # UUID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship for approval? 
    # Logic: Similar to leaves, it might need an approval flow.
    # For now, let's assume it uses the User's configured approval flow.
    
    user = relationship("User")
    reward = relationship("Reward")

class CoinLog(Base):
    __tablename__ = "coin_logs"
    __table_args__ = (
        Index("ix_coin_logs_user_created", "user_id", "created_at"),
        Index("ix_coin_logs_log_type", "log_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False) # Positive or Negative
    reason = Column(String(255), nullable=False)
    log_type = Column(String(30), nullable=True)  # mana_gift, lucky_draw, pvp, lottery, rescue, check_in, penalty, admin, system
    created_by = Column(String(100), nullable=True) # "System" or Admin Name
    sender_user_id = Column(Integer, nullable=True)  # User ID of the gift sender
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

