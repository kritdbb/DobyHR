from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ConditionType(str, enum.Enum):
    AND = "AND"
    OR = "OR"


class ApprovalFlow(Base):
    """
    Represents an approval flow assigned to a specific user.
    Each user can have one approval flow.
    """
    __tablename__ = "approval_flows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Relationships
    target_user = relationship("User", back_populates="approval_flow")
    steps = relationship(
        "ApprovalStep",
        back_populates="flow",
        cascade="all, delete-orphan",
        order_by="ApprovalStep.step_order",
    )


class ApprovalStep(Base):
    """
    Represents a single step/level in an approval flow.
    Each step has a condition type (AND/OR) and one or more approvers.
    
    AND: All approvers in this step must approve.
    OR:  Any one approver in this step can approve to pass.
    
    Steps are processed sequentially by step_order.
    """
    __tablename__ = "approval_steps"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("approval_flows.id"), nullable=False)
    step_order = Column(Integer, nullable=False)  # 1, 2, 3...
    condition_type = Column(SAEnum(ConditionType), nullable=False, default=ConditionType.AND)

    # Relationships
    flow = relationship("ApprovalFlow", back_populates="steps")
    approvers = relationship(
        "ApprovalStepApprover",
        back_populates="step",
        cascade="all, delete-orphan",
    )


class ApprovalStepApprover(Base):
    """
    Links an approver (User) to an ApprovalStep.
    Many-to-many between steps and users.
    """
    __tablename__ = "approval_step_approvers"

    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("approval_steps.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    step = relationship("ApprovalStep", back_populates="approvers")
    approver = relationship("User")
