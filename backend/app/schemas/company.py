from pydantic import BaseModel, Field
from typing import Optional


class CompanyBase(BaseModel):
    name: str = ""
    tax_id: Optional[str] = Field(None, max_length=13)
    logo: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coin_on_time: Optional[int] = 1
    coin_late_penalty: Optional[int] = 20
    coin_absent_penalty: Optional[int] = 20
    auto_coin_day: Optional[str] = None
    auto_coin_amount: Optional[int] = 0
    auto_angel_day: Optional[str] = None
    auto_angel_amount: Optional[int] = 0
    lucky_draw_day: Optional[str] = None
    lucky_draw_amount: Optional[int] = 0


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = Field(None, max_length=13)
    logo: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coin_on_time: Optional[int] = None
    coin_late_penalty: Optional[int] = None
    coin_absent_penalty: Optional[int] = None
    auto_coin_day: Optional[str] = None
    auto_coin_amount: Optional[int] = None
    auto_angel_day: Optional[str] = None
    auto_angel_amount: Optional[int] = None
    lucky_draw_day: Optional[str] = None
    lucky_draw_amount: Optional[int] = None


class CompanyResponse(CompanyBase):
    id: int

    class Config:
        from_attributes = True

