from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RedemptionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    READY = "ready"
    COMPLETED = "completed"
    REJECTED = "rejected"

class RewardBase(BaseModel):
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    point_cost: int
    is_active: bool = True

class RewardCreate(RewardBase):
    pass

class RewardUpdate(RewardBase):
    pass

class RewardResponse(RewardBase):
    id: int
    class Config:
        from_attributes = True

class CoinLogBase(BaseModel):
    amount: int
    reason: str
    created_by: Optional[str] = None

class CoinLogCreate(CoinLogBase):
    user_id: int

class CoinLogResponse(CoinLogBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class RedemptionBase(BaseModel):
    reward_id: int

class RedemptionCreate(RedemptionBase):
    pass

class RedemptionResponse(RedemptionBase):
    id: int
    user_id: int
    user_name: Optional[str] = None
    status: RedemptionStatus
    qr_code: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Include reward details
    reward: Optional[RewardResponse] = None

    class Config:
        from_attributes = True

class CoinAdjustRequest(BaseModel):
    amount: int
    reason: str
