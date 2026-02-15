from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WheelSegment(BaseModel):
    label: str
    color: str = "#f39c12"
    weight: int = 10
    reward_type: str = "gold"     # gold, mana, str, def, luk, nothing
    reward_amount: int = 0


class FortuneWheelCreate(BaseModel):
    name: str
    segments: List[WheelSegment]
    spin_min: int = 3
    spin_max: int = 7
    currency: str = "gold"   # "gold" or "mana"
    price: int = 0
    is_active: bool = False


class FortuneWheelUpdate(BaseModel):
    name: Optional[str] = None
    segments: Optional[List[WheelSegment]] = None
    spin_min: Optional[int] = None
    spin_max: Optional[int] = None
    currency: Optional[str] = None
    price: Optional[int] = None
    is_active: Optional[bool] = None


class FortuneWheelResponse(BaseModel):
    id: int
    name: str
    segments: list
    spin_min: int
    spin_max: int
    currency: str
    price: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SpinResult(BaseModel):
    segment_index: int
    segment: WheelSegment
    rotations: int        # how many full rotations
    message: str
    coins: int = 0
    angel_coins: int = 0
