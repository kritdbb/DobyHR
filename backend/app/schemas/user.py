from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time
from app.models.user import UserRole


class UserBase(BaseModel):
    name: str
    surname: str
    image: Optional[str] = None
    department: Optional[str] = None
    work_start_time: Optional[time] = None
    work_end_time: Optional[time] = None
    position: Optional[str] = None
    sick_leave_days: int = 0
    business_leave_days: int = 0
    vacation_leave_days: int = 0
    start_date: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = UserRole.STAFF
    coins: int = 0
    angel_coins: int = 0
    working_days: Optional[str] = "mon,tue,wed,thu,fri"
    status_text: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    image: Optional[str] = None
    department: Optional[str] = None
    work_start_time: Optional[time] = None
    work_end_time: Optional[time] = None
    position: Optional[str] = None
    sick_leave_days: Optional[int] = None
    business_leave_days: Optional[int] = None
    vacation_leave_days: Optional[int] = None
    start_date: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None
    working_days: Optional[str] = None


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    id: int
    name: str
    surname: str
    image: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    working_days: Optional[str] = None
    coins: int = 0
    angel_coins: int = 0

    class Config:
        from_attributes = True
