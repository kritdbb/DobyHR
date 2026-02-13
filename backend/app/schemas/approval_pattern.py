from pydantic import BaseModel
from typing import List, Optional
from app.schemas.approval import ConditionTypeEnum, ApproverResponse


# --- Pattern Step Schemas ---
class PatternStepCreate(BaseModel):
    step_order: int
    condition_type: ConditionTypeEnum = ConditionTypeEnum.AND
    approver_ids: List[int]


class PatternStepResponse(BaseModel):
    id: int
    step_order: int
    condition_type: ConditionTypeEnum
    approvers: List[ApproverResponse] = []

    class Config:
        from_attributes = True


# --- Pattern Schemas ---
class ApprovalPatternCreate(BaseModel):
    name: str
    steps: List[PatternStepCreate]


class ApprovalPatternUpdate(BaseModel):
    name: Optional[str] = None
    steps: List[PatternStepCreate]


class ApprovalPatternResponse(BaseModel):
    id: int
    name: str
    steps: List[PatternStepResponse] = []

    class Config:
        from_attributes = True


# --- Apply Pattern ---
class ApplyPatternRequest(BaseModel):
    target_user_id: int
    pattern_id: int
