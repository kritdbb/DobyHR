from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_active_admin
from app.models.user import User, UserRole
from app.models.attendance import Attendance
from app.models.leave import LeaveRequest, LeaveStatus
from app.models.company import Company
from app.models.reward import CoinLog

router = APIRouter(prefix="/api/admin", tags=["Admin Tools"])

DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


@router.post("/process-absent-penalties")
def process_absent_penalties(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Process absent penalties for a given date (default: yesterday).
    Deducts coins from users who didn't check in on their working day
    and don't have an approved leave covering that date.
    """
    # Default to yesterday (local time UTC+7)
    if not target_date:
        now_local = datetime.utcnow() + timedelta(hours=7)
        target_date = now_local.date() - timedelta(days=1)
    
    company = db.query(Company).first()
    if not company or not company.coin_absent_penalty:
        return {"message": "No absent penalty configured", "processed": 0}
    
    penalty_amount = company.coin_absent_penalty
    day_code = DAY_MAP.get(target_date.weekday(), "")
    
    # Find all staff users
    users = db.query(User).filter(User.role == UserRole.STAFF).all()
    
    penalized = []
    skipped_non_working = 0
    skipped_checked_in = 0
    skipped_on_leave = 0
    
    for user in users:
        # 1. Check if it's a working day for this user
        user_working_days = []
        if user.working_days:
            user_working_days = [d.strip().lower() for d in user.working_days.split(",")]
        
        if day_code not in user_working_days:
            skipped_non_working += 1
            continue
        
        # 2. Check if user checked in on that date
        day_start_utc = datetime.combine(target_date, datetime.min.time()) - timedelta(hours=7)
        day_end_utc = datetime.combine(target_date, datetime.max.time()) - timedelta(hours=7)
        
        attendance = db.query(Attendance).filter(
            Attendance.user_id == user.id,
            Attendance.timestamp >= day_start_utc,
            Attendance.timestamp <= day_end_utc
        ).first()
        
        if attendance:
            skipped_checked_in += 1
            continue
        
        # 3. Check if user has an approved leave covering that date
        approved_leave = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date
        ).first()
        
        if approved_leave:
            skipped_on_leave += 1
            continue
        
        # 4. Apply penalty
        user.coins -= penalty_amount
        log = CoinLog(
            user_id=user.id,
            amount=-penalty_amount,
            reason=f"Absent penalty ({target_date.isoformat()})",
            created_by="System"
        )
        db.add(log)
        penalized.append({
            "user_id": user.id,
            "name": f"{user.name} {user.surname}",
            "coins_deducted": penalty_amount,
            "new_balance": user.coins
        })
    
    db.commit()
    
    return {
        "message": f"Absent penalties processed for {target_date.isoformat()}",
        "date": target_date.isoformat(),
        "day": day_code,
        "penalty_amount": penalty_amount,
        "total_staff": len(users),
        "skipped_non_working_day": skipped_non_working,
        "skipped_checked_in": skipped_checked_in,
        "skipped_on_leave": skipped_on_leave,
        "penalized_count": len(penalized),
        "penalized_users": penalized
    }
