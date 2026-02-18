from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.core.database import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, default=5)
    rarity = Column(String(20), default="common")
    color = Column(String(20), default="#d4a44c")
    effect = Column(String(20), default="pulse")   # "pulse" | "spin"
    image = Column(String(500), nullable=True)      # uploaded image path
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
