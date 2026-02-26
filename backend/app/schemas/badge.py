from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BadgeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    stat_str: int = 0
    stat_def: int = 0
    stat_luk: int = 0


class BadgeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    stat_str: int = 0
    stat_def: int = 0
    stat_luk: int = 0
    created_at: datetime
    holder_count: Optional[int] = 0

    class Config:
        from_attributes = True


class UserBadgeResponse(BaseModel):
    id: int
    badge_id: int
    badge_name: str
    badge_image: Optional[str] = None
    badge_description: Optional[str] = None
    stat_str: int = 0
    stat_def: int = 0
    stat_luk: int = 0
    awarded_at: datetime
    awarded_by: Optional[str] = None

    class Config:
        from_attributes = True


class AwardBadgeRequest(BaseModel):
    user_ids: List[int]


class UserStatsResponse(BaseModel):
    base_str: int = 0
    base_def: int = 0
    base_luk: int = 0
    badge_str: int = 0
    badge_def: int = 0
    badge_luk: int = 0
    buff_str: int = 0
    buff_def: int = 0
    buff_luk: int = 0
    total_str: int = 0
    total_def: int = 0
    total_luk: int = 0
