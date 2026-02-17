from sqlalchemy import Column, Integer, String, Float, Text
from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="")
    tax_id = Column(String(13), nullable=True)
    logo = Column(String(500), nullable=True)  # File path to uploaded logo
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    coin_on_time = Column(Integer, default=1) # Coins for on-time check-in
    coin_late_penalty = Column(Integer, default=20) # Coins deducted for late check-in
    coin_absent_penalty = Column(Integer, default=20) # Coins deducted for not checking in on a working day
    def_grace_seconds = Column(Integer, default=0)  # DEF stat grace: 1 DEF point = X seconds before "late"
    # Auto Coin/Angel Giver
    auto_coin_day = Column(String(50), nullable=True)   # e.g. "mon,fri"
    auto_coin_amount = Column(Integer, default=0)
    auto_angel_day = Column(String(50), nullable=True)   # e.g. "mon"
    auto_angel_amount = Column(Integer, default=0)
    # Lucky Draw (weighted random by LUK)
    lucky_draw_day = Column(String(50), nullable=True)   # e.g. "mon,wed,fri"
    lucky_draw_amount = Column(Integer, default=0)
    # Step Goal: Daily
    step_daily_target = Column(Integer, default=5000)
    step_daily_str = Column(Integer, default=0)
    step_daily_def = Column(Integer, default=0)
    step_daily_luk = Column(Integer, default=0)
    step_daily_gold = Column(Integer, default=0)
    step_daily_mana = Column(Integer, default=0)
    # Step Goal: Daily Tier 2 (set target to 0 to disable)
    step_daily2_target = Column(Integer, default=0)
    step_daily2_str = Column(Integer, default=0)
    step_daily2_def = Column(Integer, default=0)
    step_daily2_luk = Column(Integer, default=0)
    step_daily2_gold = Column(Integer, default=0)
    step_daily2_mana = Column(Integer, default=0)
    # Step Goal: Monthly (set target to 0 to disable)
    step_monthly_target = Column(Integer, default=75000)
    step_monthly_str = Column(Integer, default=0)
    step_monthly_def = Column(Integer, default=0)
    step_monthly_luk = Column(Integer, default=0)
    step_monthly_gold = Column(Integer, default=1)
    step_monthly_mana = Column(Integer, default=0)
    # Rescue (Revival Pool)
    rescue_cost_per_person = Column(Integer, default=1)    # Mana cost per rescuer
    rescue_required_people = Column(Integer, default=3)    # People needed to revive
    rescue_gold_on_revive = Column(Integer, default=0)     # Gold given after revival
    # Face Recognition (CCTV Check-in)
    face_rtsp_urls = Column(Text, nullable=True)           # JSON array of RTSP URLs
    face_confidence_threshold = Column(Float, default=0.5) # Min cosine similarity
    face_min_consecutive_frames = Column(Integer, default=20)  # Consecutive frames required
    face_min_face_height = Column(Integer, default=50)     # Minimum face height in px
    face_start_time = Column(String(5), default="06:00")   # HH:MM start
    face_end_time = Column(String(5), default="10:30")     # HH:MM end
    # Man of the Month Rewards (JSON config)
    motm_rewards = Column(Text, nullable=True)  # JSON: {"motm_mana": {"gold":10,"mana":5,"str":0,"def":0,"luk":0,"badge_id":null}, ...}
