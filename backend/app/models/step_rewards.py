from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class StepReward(Base):
    __tablename__ = "step_rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_date = Column(Date, nullable=False)
    reward_type = Column(String(30), nullable=False)  # daily_2000, daily_4000, daily_8000, monthly_75000
    str_granted = Column(Integer, default=0)
    coins_granted = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "reward_date", "reward_type", name="uq_user_date_reward"),
    )
