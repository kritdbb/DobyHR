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
        leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user.id
        ).all()
        
        def calculate_days(l):
            return (l.end_date - l.start_date).days + 1

        def calculate_biz_hours(l):
            """Calculate business leave usage in hours."""
            if l.leave_start_time and l.leave_end_time:
                start_min = l.leave_start_time.hour * 60 + l.leave_start_time.minute
                end_min = l.leave_end_time.hour * 60 + l.leave_end_time.minute
                return max(0, (end_min - start_min) / 60.0)
            return ((l.end_date - l.start_date).days + 1) * 8  # Legacy: 8h per day

        sick_taken = round(sum(calculate_biz_hours(l) for l in leaves if l.leave_type == 'sick' and l.status == 'approved'), 1)
        business_taken = round(sum(calculate_biz_hours(l) for l in leaves if l.leave_type == 'business' and l.status == 'approved'), 1)
        vacation_taken = sum(calculate_days(l) for l in leaves if l.leave_type == 'vacation' and l.status == 'approved')
        total_pending = sum(1 for l in leaves if l.status == 'pending')
        
        report.append({
            "user_id": user.id,
            "user_name": f"{user.name} {user.surname}",
            "sick_taken": sick_taken,
            "sick_quota": user.sick_leave_hours or user.sick_leave_days,
            "business_taken": business_taken,
            "business_quota": user.business_leave_hours or user.business_leave_days,
            "vacation_taken": vacation_taken,
            "vacation_quota": user.vacation_leave_days,
            "total_pending": total_pending
        })
        
    return report


@router.get("/mana-gifts")
def get_mana_gift_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above)
):
    """Mana gifting statistics: per-user sent/received and transaction list."""
    from sqlalchemy import func, case

    # Build date filters
    filters = [CoinLog.reason.ilike("%Sent%Mana%to%")]
    if start_date:
        filters.append(CoinLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        filters.append(CoinLog.created_at <= datetime.combine(end_date, datetime.max.time()))

    # Get all "Sent" logs (sender side — amount is negative)
    sent_logs = (
        db.query(CoinLog)
        .options(joinedload(CoinLog.user))
        .filter(*filters)
        .order_by(CoinLog.created_at.desc())
        .all()
    )

    # Build per-user summary
    user_stats = {}
    transactions = []

    for log in sent_logs:
        sender_id = log.user_id
        sender_name = f"{log.user.name} {log.user.surname}" if log.user else "Unknown"
        amount = abs(log.amount)
        local_ts = log.created_at + timedelta(hours=7) if log.created_at else log.created_at

        # Parse recipient and delivery type from reason
        # Format: "🪽 Sent X Mana as Gold/Mana to Name Surname: comment"
        reason = log.reason or ""
        delivery_type = "gold"
        if "as Mana to" in reason:
            delivery_type = "mana"
        elif "as Gold to" in reason:
            delivery_type = "gold"

        # Extract recipient name (after "to ")
        recipient_name = ""
        if " to " in reason:
            after_to = reason.split(" to ", 1)[1]
            recipient_name = after_to.split(":")[0].strip()

        # Extract comment
        comment = ""
        if ": " in reason and reason.count(":") > 0:
            parts = reason.split(": ", 1)
            if len(parts) > 1:
                # The comment is after the last ": "
                after_to_part = reason.split(" to ", 1)[1] if " to " in reason else ""
                if ": " in after_to_part:
                    comment = after_to_part.split(": ", 1)[1]

        # Sender stats
        if sender_id not in user_stats:
            user_stats[sender_id] = {"user_id": sender_id, "user_name": sender_name, "total_sent": 0, "total_received": 0, "send_count": 0, "receive_count": 0}
        user_stats[sender_id]["total_sent"] += amount
        user_stats[sender_id]["send_count"] += 1

        transactions.append({
            "sender_id": sender_id,
            "sender_name": sender_name,
            "recipient_name": recipient_name,
            "amount": amount,
            "delivery_type": delivery_type,
            "comment": comment,
            "timestamp": local_ts,
        })

    # Now get received logs for per-user received stats
    recv_filters = [CoinLog.reason.ilike("%Received%from%")]
    if start_date:
        recv_filters.append(CoinLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        recv_filters.append(CoinLog.created_at <= datetime.combine(end_date, datetime.max.time()))

    recv_logs = (
        db.query(CoinLog)
        .options(joinedload(CoinLog.user))
        .filter(*recv_filters)
        .all()
    )

    for log in recv_logs:
        uid = log.user_id
        uname = f"{log.user.name} {log.user.surname}" if log.user else "Unknown"
        if uid not in user_stats:
            user_stats[uid] = {"user_id": uid, "user_name": uname, "total_sent": 0, "total_received": 0, "send_count": 0, "receive_count": 0}
        user_stats[uid]["total_received"] += abs(log.amount)
        user_stats[uid]["receive_count"] += 1

    return {
        "summary": sorted(user_stats.values(), key=lambda x: x["total_sent"], reverse=True),
        "transactions": transactions,
    }

