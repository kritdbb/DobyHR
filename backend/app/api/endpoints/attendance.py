from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date
import math, os, base64, uuid
from typing import Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.attendance import Attendance
from app.models.company import Company
from app.models.user import User
from app.models.reward import CoinLog
from app.models.work_request import WorkRequest, WorkRequestStatus
from app.models.badge import Badge, UserBadge
from app.models.holiday import Holiday
from app.models.location import Location
from app.api.deps import get_current_user
from pydantic import BaseModel
import logging

logger = logging.getLogger("hr-api")

from app.services.notifications import find_step_approvers, notify_approvers

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

class CheckInRequest(BaseModel):
    latitude: float
    longitude: float
    location_id: Optional[int] = None

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


def _get_total_def(user: User, db: Session) -> int:
    """Calculate total DEF = base_def + sum of badge stat_def."""
    base = user.base_def if hasattr(user, 'base_def') and user.base_def else 10
    badge_def = (
        db.query(func.coalesce(func.sum(Badge.stat_def), 0))
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .filter(UserBadge.user_id == user.id)
        .scalar()
    )
    return base + int(badge_def)


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
        Attendance.timestamp <= day_end_utc,
        Attendance.status.in_(["present", "late", "absent"])
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

    # 1b. Check if today is a holiday
    is_holiday = db.query(Holiday).filter(Holiday.date == today_local).first() is not None
    
    # 2. Check for duplicate check-in today (ignore remote_request/work_request/rejected)
    day_start_utc = datetime.combine(today_local, datetime.min.time()) - timedelta(hours=7)
    day_end_utc = datetime.combine(today_local, datetime.max.time()) - timedelta(hours=7)
    
    existing = db.query(Attendance).filter(
        Attendance.user_id == current_user.id,
        Attendance.timestamp >= day_start_utc,
        Attendance.timestamp <= day_end_utc,
        Attendance.status.in_(["present", "late", "absent"])
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You have already checked in today.")
    
    # 3. Resolve check-in location (branch → user default → company fallback)
    company = db.query(Company).first()
    checkin_loc = None
    loc_id = req.location_id or current_user.default_location_id
    if loc_id:
        checkin_loc = db.query(Location).filter(Location.id == loc_id, Location.is_active == True).first()

    if checkin_loc:
        target_lat = checkin_loc.latitude
        target_lon = checkin_loc.longitude
        max_radius = checkin_loc.radius or 200
    elif company and company.latitude and company.longitude:
        target_lat = company.latitude
        target_lon = company.longitude
        max_radius = 200
    else:
        raise HTTPException(status_code=400, detail="No check-in location configured")
    
    # 4. Calculate Distance
    distance = calculate_distance(req.latitude, req.longitude, target_lat, target_lon)
    
    # 5. Check if too far → Remote Work Request
    is_remote = distance > max_radius

    # 6. Handle non-working day or holiday → Work Request
    if not is_working_day or is_holiday:
        req_type = "holiday_request" if (is_holiday and is_working_day) else "work_request"
        detail_msg = "Holiday check-in — needs approval" if req_type == "holiday_request" else "Non-working day check-in — needs approval"

        attendance = Attendance(
            user_id=current_user.id,
            timestamp=datetime.utcnow(),
            latitude=req.latitude,
            longitude=req.longitude,
            status="work_request",
            check_in_method="gps"
        )
        db.add(attendance)
        db.flush()  # Get attendance ID

        work_req = WorkRequest(
            user_id=current_user.id,
            attendance_id=attendance.id,
            status=WorkRequestStatus.PENDING,
            request_type=req_type,
        )
        db.add(work_req)
        db.commit()

        # Notify step 1 approvers
        requester_name = f"{current_user.name} {current_user.surname or ''}".strip()
        approvers = find_step_approvers(current_user.id, 1, db)
        if approvers:
            notify_approvers(requester_name, "Work Request", detail_msg, approvers)

        logger.info(f"📋 Work Request created for {current_user.name} {current_user.surname} ({req_type})")
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
            status="remote_request",
            check_in_method="gps"
        )
        db.add(attendance)
        db.flush()

        work_req = WorkRequest(
            user_id=current_user.id,
            attendance_id=attendance.id,
            status=WorkRequestStatus.PENDING,
            request_type="remote_request",
        )
        db.add(work_req)
        db.commit()

        # Notify step 1 approvers
        requester_name = f"{current_user.name} {current_user.surname or ''}".strip()
        approvers = find_step_approvers(current_user.id, 1, db)
        if approvers:
            notify_approvers(requester_name, "Remote Work Request", f"Remote check-in (distance: {int(distance)}m) — needs approval", approvers)

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
    diff_seconds = (checkin_minutes - start_minutes) * 60
    
    # DEF grace: total_def × def_grace_seconds
    grace_seconds = 0
    if company.def_grace_seconds and company.def_grace_seconds > 0:
        total_def = _get_total_def(current_user, db)
        grace_seconds = total_def * company.def_grace_seconds
    
    if diff_seconds > 3600:  # >1hr late → absent
        status = "absent"
    elif diff_seconds > grace_seconds:  # past grace → late
        status = "late"
    
    # 8. Record Attendance
    attendance = Attendance(
        user_id=current_user.id,
        timestamp=datetime.utcnow(),
        latitude=req.latitude,
        longitude=req.longitude,
        status=status,
        check_in_method="gps"
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
            "check_in_method": r.check_in_method or "gps",
            "face_image_path": r.face_image_path,
            "face_confidence": r.face_confidence,
        })
    return result


# ═══════ Face Recognition Check-in (internal) ═══════

class FaceCheckInRequest(BaseModel):
    user_id: int
    confidence: float
    snapshot_base64: str  # Base64 JPEG of captured face


@router.post("/face-check-in")
def face_check_in(req: FaceCheckInRequest, db: Session = Depends(get_db)):
    """
    Internal endpoint called by the face recognition worker.
    No auth required — only accessible from within Docker network.
    """
    # 0. Convert UTC to Local Time (UTC+7)
    now_local = datetime.utcnow() + timedelta(hours=7)
    today_local = now_local.date()

    # 1. Check duplicate check-in today
    day_start_utc = datetime.combine(today_local, datetime.min.time()) - timedelta(hours=7)
    day_end_utc = datetime.combine(today_local, datetime.max.time()) - timedelta(hours=7)

    existing = db.query(Attendance).filter(
        Attendance.user_id == req.user_id,
        Attendance.timestamp >= day_start_utc,
        Attendance.timestamp <= day_end_utc
    ).first()

    if existing:
        return {"message": "Already checked in today", "skipped": True}

    # 2. Get user
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 3. Check if today is a working day
    is_working_day = True
    if user.working_days:
        day_code = DAY_MAP.get(today_local.weekday(), "")
        user_working_days = [d.strip().lower() for d in user.working_days.split(",")]
        if day_code not in user_working_days:
            is_working_day = False

    if not is_working_day:
        return {"message": "Not a working day for this user", "skipped": True}

    # 4. Save face snapshot
    snapshot_path = None
    try:
        img_data = base64.b64decode(req.snapshot_base64)
        snapshot_filename = f"face_checkin_{req.user_id}_{uuid.uuid4().hex[:8]}.jpg"
        snapshot_dir = os.path.join(settings.UPLOAD_DIR, "face_checkins")
        os.makedirs(snapshot_dir, exist_ok=True)
        snapshot_full_path = os.path.join(snapshot_dir, snapshot_filename)
        with open(snapshot_full_path, "wb") as f:
            f.write(img_data)
        snapshot_path = f"/uploads/face_checkins/{snapshot_filename}"
    except Exception as e:
        logger.warning(f"⚠️ Failed to save face snapshot: {e}")

    # 5. Determine on-time / late / absent
    check_in_time = now_local.time()
    status = "present"
    from datetime import time as dt_time
    start = user.work_start_time or dt_time(9, 0)
    start_minutes = start.hour * 60 + start.minute
    checkin_minutes = check_in_time.hour * 60 + check_in_time.minute
    diff_seconds = (checkin_minutes - start_minutes) * 60

    # DEF grace: total_def × def_grace_seconds
    grace_seconds = 0
    if company and company.def_grace_seconds and company.def_grace_seconds > 0:
        total_def = _get_total_def(user, db)
        grace_seconds = total_def * company.def_grace_seconds

    if diff_seconds > 3600:
        status = "absent"
    elif diff_seconds > grace_seconds:
        status = "late"

    # 6. Get company location for lat/lon
    company = db.query(Company).first()
    lat = company.latitude if company else 0.0
    lon = company.longitude if company else 0.0

    # 7. Record Attendance
    attendance = Attendance(
        user_id=req.user_id,
        timestamp=datetime.utcnow(),
        latitude=lat,
        longitude=lon,
        status=status,
        check_in_method="face",
        face_image_path=snapshot_path,
        face_confidence=req.confidence,
    )
    db.add(attendance)

    # 8. Coin Logic (same as GPS check-in)
    coin_change = 0
    coin_reason = ""

    if company:
        if status == "absent":
            if company.coin_absent_penalty:
                coin_change = -company.coin_absent_penalty
                coin_reason = "Absent (face check-in >1hr late)"
        elif status == "late":
            if company.coin_late_penalty:
                coin_change = -company.coin_late_penalty
                coin_reason = "Late (face check-in)"
        else:
            if company.coin_on_time:
                coin_change = company.coin_on_time
                coin_reason = "On-time (face check-in)"

        if coin_change != 0:
            user.coins += coin_change
            log = CoinLog(
                user_id=req.user_id,
                amount=coin_change,
                reason=coin_reason,
                created_by="Face Recognition"
            )
            db.add(log)

    db.commit()
    logger.info(f"📸 Face check-in: {user.name} {user.surname} — {status} (confidence: {req.confidence:.3f})")
    return {
        "message": "Face check-in successful",
        "user_id": req.user_id,
        "status": status,
        "confidence": req.confidence,
        "coin_change": coin_change,
        "skipped": False,
    }
