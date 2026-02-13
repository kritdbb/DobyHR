from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.approval import ConditionType


class ApprovalPattern(Base):
    """Reusable approval pattern template."""
    __tablename__ = "approval_patterns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    steps = relationship(
        "ApprovalPatternStep",
        back_populates="pattern",
        cascade="all, delete-orphan",
        order_by="ApprovalPatternStep.step_order",
    )


class ApprovalPatternStep(Base):
    """A step within an approval pattern."""
    __tablename__ = "approval_pattern_steps"

    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(Integer, ForeignKey("approval_patterns.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    condition_type = Column(SAEnum(ConditionType), nullable=False, default=ConditionType.AND)

    pattern = relationship("ApprovalPattern", back_populates="steps")
    approvers = relationship(
        "ApprovalPatternStepApprover",
        back_populates="step",
        cascade="all, delete-orphan",
    )


class ApprovalPatternStepApprover(Base):
    """Links an approver to a pattern step."""
    __tablename__ = "approval_pattern_step_approvers"

    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("approval_pattern_steps.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    step = relationship("ApprovalPatternStep", back_populates="approvers")
    approver = relationship("User")
