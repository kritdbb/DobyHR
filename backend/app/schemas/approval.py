from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class ConditionTypeEnum(str, Enum):
    AND = "AND"
    OR = "OR"


# --- Approver Schemas ---
class ApproverInfo(BaseModel):
    approver_id: int

    class Config:
        from_attributes = True


class ApproverResponse(BaseModel):
    id: int
    approver_id: int
    approver_name: Optional[str] = None
    approver_surname: Optional[str] = None

    class Config:
        from_attributes = True


# --- Step Schemas ---
class ApprovalStepCreate(BaseModel):
    step_order: int
    condition_type: ConditionTypeEnum = ConditionTypeEnum.AND
    approver_ids: List[int]


class ApprovalStepResponse(BaseModel):
    id: int
    step_order: int
    condition_type: ConditionTypeEnum
    approvers: List[ApproverResponse] = []

    class Config:
        from_attributes = True


# --- Flow Schemas ---
class ApprovalFlowCreate(BaseModel):
    name: Optional[str] = None
    target_user_id: int
    steps: List[ApprovalStepCreate]


class ApprovalFlowUpdate(BaseModel):
    name: Optional[str] = None
    steps: List[ApprovalStepCreate]


class ApprovalFlowResponse(BaseModel):
    id: int
    name: Optional[str] = None
    target_user_id: int
    target_user_name: Optional[str] = None
    steps: List[ApprovalStepResponse] = []

    class Config:
        from_attributes = True
