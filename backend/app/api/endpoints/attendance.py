from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
import math
from app.core.database import get_db
from app.models.attendance import Attendance
from app.models.company import Company
from app.models.user import User
from app.models.reward import CoinLog
from app.models.work_request import WorkRequest, WorkRequestStatus
from app.api.deps import get_current_user
from pydantic import BaseModel
import logging

logger = logging.getLogger("hr-api")

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

class CheckInRequest(BaseModel):
    latitude: float
    longitude: float

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 * 1000 # Meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


@router.get("/today-status")
def get_today_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if user has already checked in today. Returns the record or null."""
    now_local = datetime.utcnow() + timedelta(hours=7)
    today_local = now_local.date()
    day_start_utc = datetime.combine(today_local, datetime.min.time()) - timedelta(hours=7)
    day_end_utc = datetime.combine(today_local, datetime.max.time()) - timedelta(hours=7)

    existing = db.query(Attendance).filter(
        Attendance.user_id == current_user.id,
        Attendance.timestamp >= day_start_utc,
        Attendance.timestamp <= day_end_utc
    ).first()

    if existing:
        checkin_local = existing.timestamp + timedelta(hours=7)
        return {
            "checked_in": True,
            "time": checkin_local.strftime("%H:%M"),
            "status": existing.status,
            "timestamp": checkin_local,
        }
    return {"checked_in": False}


@router.post("/check-in")
def check_in(
    req: CheckInRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 0. Convert UTC to Local Time (UTC+7 for Thailand)
    now_local = datetime.utcnow() + timedelta(hours=7)
    today_local = now_local.date()
    
    # 1. Check if today is a working day for this user
    is_working_day = True
    if current_user.working_days:
        day_code = DAY_MAP.get(today_local.weekday(), "")
        user_working_days = [d.strip().lower() for d in current_user.working_days.split(",")]
        if day_code not in user_working_days:
            is_working_day = False
    
    # 2. Check for duplicate check-in today
    day_start_utc = datetime.combine(today_local, datetime.min.time()) - timedelta(hours=7)
    day_end_utc = datetime.combine(today_local, datetime.max.time()) - timedelta(hours=7)
    
    existing = db.query(Attendance).filter(
        Attendance.user_id == current_user.id,
        Attendance.timestamp >= day_start_utc,
        Attendance.timestamp <= day_end_utc
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You have already checked in today.")
    
    # 3. Get Company Location
    company = db.query(Company).first()
    if not company or not company.latitude or not company.longitude:
        raise HTTPException(status_code=400, detail="Company location not set in settings")
    
    # 4. Calculate Distance
    distance = calculate_distance(req.latitude, req.longitude, company.latitude, company.longitude)
    
    # 5. Check if too far → Remote Work Request
    is_remote = distance > 200

    # 6. Handle non-working day → Work Request
    if not is_working_day:
        attendance = Attendance(
            user_id=current_user.id,
            timestamp=datetime.utcnow(),
            latitude=req.latitude,
            longitude=req.longitude,
            status="work_request"
        )
        db.add(attendance)
        db.flush()  # Get attendance ID

        work_req = WorkRequest(
            user_id=current_user.id,
            attendance_id=attendance.id,
            status=WorkRequestStatus.PENDING
        )
        db.add(work_req)
        db.commit()

        logger.info(f"📋 Work Request created for {current_user.name} {current_user.surname} (non-working day)")
        return {
            "message": "Work Request created — awaiting approval before coins are granted.",
            "distance": int(distance),
            "timestamp": now_local,
            "status": "work_request",
            "coin_change": 0,
            "coins": current_user.coins,
            "work_request_created": True,
        }

    # 6b. Handle remote check-in (too far) → Remote Work Request
    if is_remote:
        attendance = Attendance(
            user_id=current_user.id,
            timestamp=datetime.utcnow(),
            latitude=req.latitude,
            longitude=req.longitude,
            status="remote_request"
        )
        db.add(attendance)
        db.flush()

        work_req = WorkRequest(
            user_id=current_user.id,
            attendance_id=attendance.id,
            status=WorkRequestStatus.PENDING
        )
        db.add(work_req)
        db.commit()

        logger.info(f"📋 Remote Work Request created for {current_user.name} {current_user.surname} (distance: {int(distance)}m)")
        return {
            "message": "Remote Work Request created — awaiting manager approval.",
            "distance": int(distance),
            "timestamp": now_local,
            "status": "remote_request",
            "coin_change": 0,
            "coins": current_user.coins,
            "remote_request_created": True,
        }

    # 7. Determine on-time / late / absent (working day, in range)
    check_in_time = now_local.time()
    status = "present"
    
    # Use work_start_time or default to 09:00
    from datetime import time as dt_time
    start = current_user.work_start_time or dt_time(9, 0)
    start_minutes = start.hour * 60 + start.minute
    checkin_minutes = check_in_time.hour * 60 + check_in_time.minute
    diff = checkin_minutes - start_minutes
    
    if diff > 60:
        status = "absent"
    elif diff > 0:
        status = "late"
    
    # 8. Record Attendance
    attendance = Attendance(
        user_id=current_user.id,
        timestamp=datetime.utcnow(),
        latitude=req.latitude,
        longitude=req.longitude,
        status=status
    )
    db.add(attendance)

    # 9. Coin Logic
    coin_change = 0
    coin_reason = ""
    
    if status == "absent":
        if company.coin_absent_penalty:
            coin_change = -company.coin_absent_penalty
            coin_reason = "Absent (checked in >1hr late)"
    elif status == "late":
        if company.coin_late_penalty:
            coin_change = -company.coin_late_penalty
            coin_reason = "Late Check-in"
    else:
        if company.coin_on_time:
            coin_change = company.coin_on_time
            coin_reason = "On-time Check-in"
    
    if coin_change != 0:
        current_user.coins += coin_change
        log = CoinLog(
            user_id=current_user.id,
            amount=coin_change,
            reason=coin_reason,
            created_by="System"
        )
        db.add(log)

    db.commit()
    return {
        "message": "Check-in successful", 
        "distance": int(distance), 
        "timestamp": now_local,
        "status": status,
        "coin_change": coin_change,
        "coins": current_user.coins
    }

@router.get("/my-history")
def get_my_attendance(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(Attendance).filter(Attendance.user_id == current_user.id).order_by(Attendance.timestamp.desc()).all()
    result = []
    for r in records:
        local_ts = r.timestamp + timedelta(hours=7) if r.timestamp else None
        result.append({
            "id": r.id,
            "user_id": r.user_id,
            "timestamp": local_ts,
            "status": r.status,
            "latitude": r.latitude,
            "longitude": r.longitude,
        })
    return result

