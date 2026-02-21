from sqlalchemy import Column, Integer, String, Date, DateTime
from app.core.database import Base
from datetime import datetime


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
