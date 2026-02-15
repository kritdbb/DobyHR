from sqlalchemy import Column, Integer, String, Date, Time
from sqlalchemy.orm import relationship
import enum
from sqlalchemy import Enum as SQLAlchemyEnum
from app.core.database import Base


class UserRole(str, enum.Enum):
    GOD = "god"
    GM = "gm"
    PLAYER = "player"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=True)  # เบอร์มือถือ
    hashed_password = Column(String(255), nullable=True)
    role = Column(SQLAlchemyEnum(UserRole, values_callable=lambda x: [e.value for e in x]), default=UserRole.PLAYER)
    image = Column(String(500), nullable=True)  # File path to uploaded image
    department = Column(String(100), nullable=True)  # แผนก
    work_start_time = Column(Time, nullable=True)  # เวลาเริ่มงาน
    work_end_time = Column(Time, nullable=True)  # เวลาเลิกงาน
    position = Column(String(100), nullable=True)  # ตำแหน่ง
    sick_leave_days = Column(Integer, default=0)  # จำนวนลาป่วย
    business_leave_days = Column(Integer, default=0)  # จำนวนลากิจ
    vacation_leave_days = Column(Integer, default=0)  # จำนวนลาพักร้อน
    start_date = Column(Date, nullable=True)  # วันที่เริ่มงาน
    coins = Column(Integer, default=0)  # Coin balance
    angel_coins = Column(Integer, default=0)  # Angel Coin balance
    base_str = Column(Integer, default=10)  # Base Strength
    base_def = Column(Integer, default=10)  # Base Defense
    base_luk = Column(Integer, default=10)  # Base Luck
    working_days = Column(String(50), default="mon,tue,wed,thu,fri")  # Comma-separated: mon,tue,wed,thu,fri,sat,sun
    status_text = Column(String(70), nullable=True)  # Custom status from Title Scroll

    # Relationship to approval flow
    approval_flow = relationship(
        "ApprovalFlow", back_populates="target_user", uselist=False
    )
