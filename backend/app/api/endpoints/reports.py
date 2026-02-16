from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_gm_or_above
from app.models.user import User
from app.models.attendance import Attendance
from app.models.reward import CoinLog
from app.models.leave import LeaveRequest

from pydantic import BaseModel

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# --- Schemas for Reports ---

class AttendanceReportItem(BaseModel):
    id: int
    user_id: int
    user_name: str
    timestamp: datetime
    status: str
    check_in_method: Optional[str] = "gps"
    face_image_path: Optional[str] = None
    face_confidence: Optional[float] = None

    class Config:
        from_attributes = True

class CoinReportItem(BaseModel):
    id: int
    user_id: int
    user_name: str
    amount: int
    reason: str
    created_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LeaveSummaryItem(BaseModel):
    user_id: int
    user_name: str
    sick_taken: int
    sick_quota: int
    business_taken: int
    business_quota: int
    vacation_taken: int
    vacation_quota: int
    total_pending: int

# --- Endpoints ---

@router.get("/attendance", response_model=List[AttendanceReportItem])
def get_attendance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above)
):
    query = db.query(Attendance).options(joinedload(Attendance.user))
    
    if user_ids:
        query = query.filter(Attendance.user_id.in_(user_ids))
    
    if start_date:
        # Convert date to datetime start
        dt_start = datetime.combine(start_date, datetime.min.time())
        query = query.filter(Attendance.timestamp >= dt_start)
    
    if end_date:
        # Convert date to datetime end
        dt_end = datetime.combine(end_date, datetime.max.time())
        query = query.filter(Attendance.timestamp <= dt_end)
        
    results = query.order_by(Attendance.timestamp.desc()).all()
    
    # Map to schema manually or let Pydantic handle it if structure matches
    # We need user_name which is on the relation
    report = []
    for r in results:
        local_ts = r.timestamp + timedelta(hours=7) if r.timestamp else r.timestamp
        report.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": f"{r.user.name} {r.user.surname}" if r.user else "Unknown",
            "timestamp": local_ts,
            "status": r.status,
            "check_in_method": r.check_in_method or "gps",
            "face_image_path": r.face_image_path,
            "face_confidence": r.face_confidence,
        })
    return report

@router.get("/coins", response_model=List[CoinReportItem])
def get_coin_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above)
):
    query = db.query(CoinLog).options(joinedload(CoinLog.user))
    
    if user_ids:
        query = query.filter(CoinLog.user_id.in_(user_ids))
        
    if start_date:
        dt_start = datetime.combine(start_date, datetime.min.time())
        query = query.filter(CoinLog.created_at >= dt_start)
        
    if end_date:
        dt_end = datetime.combine(end_date, datetime.max.time())
        query = query.filter(CoinLog.created_at <= dt_end)
        
    results = query.order_by(CoinLog.created_at.desc()).all()
    
    report = []
    for r in results:
        local_ts = r.created_at + timedelta(hours=7) if r.created_at else r.created_at
        report.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": f"{r.user.name} {r.user.surname}" if r.user else "Unknown",
            "amount": r.amount,
            "reason": r.reason,
            "created_by": r.created_by,
            "created_at": local_ts
        })
    return report

@router.get("/leaves", response_model=List[LeaveSummaryItem])
def get_leave_summary_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above)
):
    # This report summarizes leave usage per user
    users = db.query(User).all()
    
    report = []
    for user in users:
        # Calculate taken leaves (Approved)
        # Note: In a real system, we might query LeaveRequest table with aggregation.
        # But User model has summary columns? No, User model has 'days' which are QUOTAS usually? 
        # Let's check User model.
        # User model: sick_leave_days (Quota), etc.
        # We need check ACTUAL usage.
        
        # Query LeaveRequests for this user
        leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user.id
        ).all()
        
        def calculate_days(l):
            return (l.end_date - l.start_date).days + 1

        sick_taken = sum(calculate_days(l) for l in leaves if l.leave_type == 'sick' and l.status == 'approved')
        business_taken = sum(calculate_days(l) for l in leaves if l.leave_type == 'business' and l.status == 'approved')
        vacation_taken = sum(calculate_days(l) for l in leaves if l.leave_type == 'vacation' and l.status == 'approved')
        total_pending = sum(1 for l in leaves if l.status == 'pending')
        
        report.append({
            "user_id": user.id,
            "user_name": f"{user.name} {user.surname}",
            "sick_taken": sick_taken,
            "sick_quota": user.sick_leave_days,
            "business_taken": business_taken,
            "business_quota": user.business_leave_days,
            "vacation_taken": vacation_taken,
            "vacation_quota": user.vacation_leave_days,
            "total_pending": total_pending
        })
        
    return report
