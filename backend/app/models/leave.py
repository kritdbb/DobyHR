from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class LeaveType(str, enum.Enum):
    SICK = "sick"
    BUSINESS = "business"
    VACATION = "vacation"

class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_EVIDENCE = "pending_evidence"

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    leave_type = Column(SQLAlchemyEnum(LeaveType))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(500), nullable=True)
    status = Column(SQLAlchemyEnum(LeaveStatus), default=LeaveStatus.PENDING)
    # Time-range for business/sick leave
    leave_start_time = Column(Time, nullable=True)  # e.g. 08:30
    leave_end_time = Column(Time, nullable=True)    # e.g. 10:00
    # Evidence image for sick leave
    evidence_image = Column(String(500), nullable=True)
    
    user = relationship("User", backref="leave_requests")
