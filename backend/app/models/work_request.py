from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum


class WorkRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class WorkRequest(Base):
    __tablename__ = "work_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    attendance_id = Column(Integer, ForeignKey("attendance.id"), nullable=True)
    status = Column(SAEnum(WorkRequestStatus), default=WorkRequestStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    attendance = relationship("Attendance")
