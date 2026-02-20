from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from datetime import datetime


class ExpenseType(str, enum.Enum):
    GENERAL = "GENERAL"
    TRAVEL = "TRAVEL"
    CENTER = "CENTER"


class VehicleType(str, enum.Enum):
    CAR = "CAR"
    MOTORCYCLE = "MOTORCYCLE"


class ExpenseStatus(str, enum.Enum):
    PENDING = "PENDING"
    ALL_APPROVED = "ALL_APPROVED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class ExpenseRequest(Base):
    __tablename__ = "expense_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expense_type = Column(SAEnum(ExpenseType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    status = Column(SAEnum(ExpenseStatus, values_callable=lambda x: [e.value for e in x]), default=ExpenseStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    # --- General Expense fields ---
    expense_date = Column(Date, nullable=True)
    description = Column(String(500), nullable=True)
    amount = Column(Float, default=0)
    file_path = Column(String(500), nullable=True)  # single file (image or PDF)

    # --- Travel Expense fields ---
    travel_date = Column(Date, nullable=True)
    vehicle_type = Column(SAEnum(VehicleType, values_callable=lambda x: [e.value for e in x]), nullable=True)
    km_outbound = Column(Float, default=0)
    km_return = Column(Float, default=0)
    travel_cost = Column(Float, default=0)  # auto-calculated
    other_cost = Column(Float, default=0)   # manual entry
    total_amount = Column(Float, default=0) # travel_cost + other_cost
    outbound_image = Column(String(500), nullable=True)
    return_image = Column(String(500), nullable=True)

    # --- Approval tracking ---
    current_step = Column(Integer, default=0)   # how many steps approved
    total_steps = Column(Integer, default=0)     # total steps from approval flow
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)

    # Center expense: who actually submitted the slip
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="expense_requests")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    attachments = relationship("ExpenseAttachment", back_populates="expense", cascade="all, delete-orphan")


class ExpenseAttachment(Base):
    """Extra attachments for travel expense 'other costs'."""
    __tablename__ = "expense_attachments"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expense_requests.id"), nullable=False)
    file_path = Column(String(500), nullable=False)

    expense = relationship("ExpenseRequest", back_populates="attachments")
