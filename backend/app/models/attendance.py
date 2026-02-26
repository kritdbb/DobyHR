from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, String, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        Index("ix_attendance_user_timestamp", "user_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String(50), default="present")  # "present", "late", etc.
    check_in_method = Column(String(20), default="gps")  # "gps" or "face"
    face_image_path = Column(String(500), nullable=True)  # snapshot of recognized face
    face_confidence = Column(Float, nullable=True)  # cosine similarity score
    
    user = relationship("User", backref="attendances")

