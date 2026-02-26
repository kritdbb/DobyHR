from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta, time as dt_time
from typing import List, Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.leave import LeaveRequest, LeaveType, LeaveStatus
from app.models.user import User
from app.models.attendance import Attendance
from app.models.company import Company
from app.models.reward import CoinLog
from app.models.approval import ApprovalFlow, ApprovalStep, ApprovalStepApprover
from app.api.deps import get_current_user, get_current_gm_or_above
from pydantic import BaseModel
import logging, os, uuid

logger = logging.getLogger("hr-api")

from app.services.notifications import find_step_approvers, notify_approvers

router = APIRouter(prefix="/api/leaves", tags=["Leaves"])

class LeaveRequestCreate(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    # Time-range (required for business and sick leave)
    start_time: Optional[str] = None  # "HH:MM" e.g. "08:30"
    end_time: Optional[str] = None    # "HH:MM" e.g. "10:00"

class LeaveRequestResponse(BaseModel):
    id: int
    user_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatus
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    evidence_image: Optional[str] = None

    class Config:
        from_attributes = True

def _parse_time(t_str: Optional[str]) -> Optional[dt_time]:
    """Parse 'HH:MM' string to time object."""
    if not t_str:
        return None
    parts = t_str.strip().split(":")
    return dt_time(int(parts[0]), int(parts[1]))

def _time_to_str(t: Optional[dt_time]) -> Optional[str]:
    """Convert time object to 'HH:MM' string."""
    if not t:
        return None
    return f"{t.hour:02d}:{t.minute:02d}"

def _calc_hours(start_t: dt_time, end_t: dt_time) -> float:
    """Calculate hours between two times."""
    start_min = start_t.hour * 60 + start_t.minute
    end_min = end_t.hour * 60 + end_t.minute
    return max(0, (end_min - start_min) / 60.0)

def _leave_to_response(leave: LeaveRequest) -> dict:
    """Convert LeaveRequest ORM to response dict with time strings."""
    return {
        "id": leave.id,
        "user_id": leave.user_id,
        "leave_type": leave.leave_type,
        "start_date": leave.start_date,
        "end_date": leave.end_date,
        "reason": leave.reason,
        "status": leave.status,
        "start_time": _time_to_str(leave.leave_start_time),
        "end_time": _time_to_str(leave.leave_end_time),
        "evidence_image": leave.evidence_image,
    }

def _count_hours_used(user_id: int, leave_type: LeaveType, db: Session) -> float:
    """Count total leave hours used (non-rejected) for a given type."""
    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.leave_type == leave_type,
        LeaveRequest.status != LeaveStatus.REJECTED
    ).all()
    total = 0.0
    for leave in leaves:
        if leave.leave_start_time and leave.leave_end_time:
            total += _calc_hours(leave.leave_start_time, leave.leave_end_time)
        else:
            # Legacy: treat each day as 8 hours
            total += ((leave.end_date - leave.start_date).days + 1) * 8
    return total


@router.post("/request")
def request_leave(
    req: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Validation
    if req.end_date < req.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    # 2. Business & Sick leave: time-range validation (same logic)
    if req.leave_type in (LeaveType.BUSINESS, LeaveType.SICK):
        if not req.start_time or not req.end_time:
            raise HTTPException(status_code=400, detail=f"{req.leave_type.value} leave requires start_time and end_time")
        if req.start_date != req.end_date:
            raise HTTPException(status_code=400, detail=f"{req.leave_type.value} leave must be single-day. Submit separate requests for multi-day.")
        
        start_t = _parse_time(req.start_time)
        end_t = _parse_time(req.end_time)
        if not start_t or not end_t:
            raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
        if end_t <= start_t:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        # Calculate hours used
        hours_requested = _calc_hours(start_t, end_t)
        
        # Check quota (hours)
        used_hours = _count_hours_used(current_user.id, req.leave_type, db)
        if req.leave_type == LeaveType.BUSINESS:
            quota_hours = current_user.business_leave_hours or 0
        else:
            quota_hours = current_user.sick_leave_hours or 0
        
        if used_hours + hours_requested > quota_hours:
            remaining = max(0, quota_hours - used_hours)
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient {req.leave_type.value} leave quota. Remaining: {remaining:.1f}h, Requested: {hours_requested:.1f}h"
            )
        
        leave_request = LeaveRequest(
            user_id=current_user.id,
            leave_type=req.leave_type,
            start_date=req.start_date,
            end_date=req.end_date,
            reason=req.reason,
            status=LeaveStatus.PENDING,
            leave_start_time=start_t,
            leave_end_time=end_t,
        )
    else:
        # Vacation: date-based (same as before)
        duration = (req.end_date - req.start_date).days + 1
        
        used_days = 0
        past_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == current_user.id,
            LeaveRequest.leave_type == req.leave_type,
            LeaveRequest.status != LeaveStatus.REJECTED
        ).all()
        for leave in past_leaves:
            days = (leave.end_date - leave.start_date).days + 1
            used_days += days

        quota = current_user.vacation_leave_days

        if used_days + duration > quota:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient leave quota. Remaining: {quota - used_days}, Requested: {duration}"
            )
        
        leave_request = LeaveRequest(
            user_id=current_user.id,
            leave_type=req.leave_type,
            start_date=req.start_date,
            end_date=req.end_date,
            reason=req.reason,
            status=LeaveStatus.PENDING,
        )

    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)

    # Notify step 1 approvers
    requester_name = f"{current_user.name} {current_user.surname or ''}".strip()
    approvers = find_step_approvers(current_user.id, 1, db)
    if approvers:
        if req.leave_type in (LeaveType.BUSINESS, LeaveType.SICK):
            detail = f"{req.leave_type.value} leave: {req.start_date} ({req.start_time}–{req.end_time}). Reason: {req.reason}"
        else:
            detail = f"{req.leave_type.value} leave: {req.start_date} → {req.end_date}. Reason: {req.reason}"
        notify_approvers(requester_name, "Leave Request", detail, approvers)

    return _leave_to_response(leave_request)


@router.get("/my-leaves")
def get_my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == current_user.id
    ).order_by(LeaveRequest.start_date.desc()).all()
    return [_leave_to_response(l) for l in leaves]

@router.get("/quota")
def get_leave_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    def count_used_days(l_type):
        leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == current_user.id,
            LeaveRequest.leave_type == l_type,
            LeaveRequest.status != LeaveStatus.REJECTED
        ).all()
        return sum([(l.end_date - l.start_date).days + 1 for l in leaves])

    sick_used_hours = _count_hours_used(current_user.id, LeaveType.SICK, db)
    sick_total_hours = current_user.sick_leave_hours or 0

    business_used_hours = _count_hours_used(current_user.id, LeaveType.BUSINESS, db)
    business_total_hours = current_user.business_leave_hours or 0

    return {
        "sick": {
            "total": sick_total_hours,
            "used": round(sick_used_hours, 1),
            "unit": "hours",
        },
        "business": {
            "total": business_total_hours,
            "used": round(business_used_hours, 1),
            "unit": "hours",
        },
        "vacation": {"total": current_user.vacation_leave_days, "used": count_used_days(LeaveType.VACATION)},
    }

@router.get("/all")
def get_all_leaves(
    status: LeaveStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above)
):
    query = db.query(LeaveRequest).order_by(LeaveRequest.start_date.desc())
    if status:
        query = query.filter(LeaveRequest.status == status)
    return [_leave_to_response(l) for l in query.all()]


@router.put("/{leave_id}/approve")
def approve_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot approve a leave that is already {leave.status.value}")
    
    # Sick leave: first approval → PENDING_EVIDENCE (need photo)
    if leave.leave_type == LeaveType.SICK and not leave.evidence_image:
        leave.status = LeaveStatus.PENDING_EVIDENCE
    else:
        leave.status = LeaveStatus.APPROVED

    # ── Sick Leave Coin Refund (only when truly APPROVED) ──
    if leave.status == LeaveStatus.APPROVED and leave.leave_type == LeaveType.SICK:
        user = db.query(User).filter(User.id == leave.user_id).first()
        total_refund = 0

        current_date = leave.start_date
        while current_date <= leave.end_date:
            date_str = current_date.isoformat()
            
            penalty_log = db.query(CoinLog).filter(
                CoinLog.user_id == leave.user_id,
                CoinLog.reason.like(f"%Absent penalty ({date_str})%"),
                CoinLog.amount < 0,
            ).first()

            if penalty_log:
                refund_amount = abs(penalty_log.amount)
                total_refund += refund_amount
                logger.info(f"💰 Refunding {refund_amount} coins to {user.name} for {date_str} (sick leave approved)")

            current_date += timedelta(days=1)

        if total_refund > 0:
            user.coins += total_refund
            refund_log = CoinLog(
                user_id=user.id,
                amount=total_refund,
                reason=f"Sick leave approved — refund for absent penalties ({leave.start_date} to {leave.end_date})",
                created_by=f"{current_user.name} {current_user.surname}",
            )
            db.add(refund_log)
            logger.info(f"✅ Total refund: {total_refund} coins for {user.name} {user.surname}")

    db.commit()
    db.refresh(leave)
    return _leave_to_response(leave)


@router.put("/{leave_id}/reject")
def reject_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.status not in (LeaveStatus.PENDING, LeaveStatus.PENDING_EVIDENCE):
        raise HTTPException(status_code=400, detail=f"Cannot reject a leave that is already {leave.status.value}")
    
    leave.status = LeaveStatus.REJECTED

    # Sick leave rejection with evidence → apply absent penalty
    if leave.leave_type == LeaveType.SICK:
        company = db.query(Company).first()
        if company and company.coin_absent_penalty:
            user = db.query(User).filter(User.id == leave.user_id).first()
            if user:
                penalty = company.coin_absent_penalty
                user.coins -= penalty
                log = CoinLog(
                    user_id=user.id,
                    amount=-penalty,
                    reason=f"Sick leave rejected — absent penalty ({leave.start_date.isoformat()})",
                    created_by=f"{current_user.name} {current_user.surname}",
                )
                db.add(log)
                logger.info(f"❌ Sick leave rejected: {penalty} coins deducted from {user.name} for {leave.start_date}")

    db.commit()
    db.refresh(leave)
    return _leave_to_response(leave)


@router.post("/{leave_id}/upload-evidence")
async def upload_leave_evidence(
    leave_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload/replace evidence image for sick leave. Does NOT change status yet."""
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only upload evidence for your own leave")
    if leave.status != LeaveStatus.PENDING_EVIDENCE:
        raise HTTPException(status_code=400, detail=f"Leave is not in pending_evidence status (current: {leave.status.value})")
    
    # Save file
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"leave_evidence_{leave_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    leave.evidence_image = f"/uploads/{filename}"
    # Status stays as PENDING_EVIDENCE — user must click submit separately
    
    db.commit()
    db.refresh(leave)
    return _leave_to_response(leave)


@router.put("/{leave_id}/submit-evidence")
def submit_leave_evidence(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit evidence for re-approval. Requires evidence_image to be uploaded first."""
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only submit evidence for your own leave")
    if leave.status != LeaveStatus.PENDING_EVIDENCE:
        raise HTTPException(status_code=400, detail=f"Leave is not in pending_evidence status")
    if not leave.evidence_image:
        raise HTTPException(status_code=400, detail="Please upload evidence image first")
    
    leave.status = LeaveStatus.PENDING
    db.commit()
    db.refresh(leave)

    # Notify approvers for re-approval
    requester_name = f"{current_user.name} {current_user.surname or ''}".strip()
    approvers = find_step_approvers(current_user.id, 1, db)
    if approvers:
        detail = f"Sick leave evidence uploaded for {leave.start_date}. Please re-approve."
        notify_approvers(requester_name, "Sick Leave Evidence", detail, approvers)

    return _leave_to_response(leave)


class PendingLeaveApprovalResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatus
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    evidence_image: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/pending-approvals", response_model=List[PendingLeaveApprovalResponse])
def get_pending_leave_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pending leave requests from users that the current user is an approver for."""
    target_user_ids = (
        db.query(ApprovalFlow.target_user_id)
        .join(ApprovalStep, ApprovalStep.flow_id == ApprovalFlow.id)
        .join(ApprovalStepApprover, ApprovalStepApprover.step_id == ApprovalStep.id)
        .filter(ApprovalStepApprover.approver_id == current_user.id)
        .distinct()
        .all()
    )
    user_ids = [uid for (uid,) in target_user_ids]

    if not user_ids:
        return []

    leaves = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.user_id.in_(user_ids),
            LeaveRequest.status == LeaveStatus.PENDING,
        )
        .order_by(LeaveRequest.start_date.desc())
        .all()
    )

    result = []
    user_cache = {}
    for leave in leaves:
        if leave.user_id not in user_cache:
            u = db.query(User).filter(User.id == leave.user_id).first()
            user_cache[leave.user_id] = f"{u.name} {u.surname}" if u else "Unknown"
        result.append(
            PendingLeaveApprovalResponse(
                id=leave.id,
                user_id=leave.user_id,
                user_name=user_cache[leave.user_id],
                leave_type=leave.leave_type,
                start_date=leave.start_date,
                end_date=leave.end_date,
                reason=leave.reason,
                status=leave.status,
                start_time=_time_to_str(leave.leave_start_time),
                end_time=_time_to_str(leave.leave_end_time),
                evidence_image=leave.evidence_image,
            )
        )
    return result


@router.get("/today-business-leave")
def get_today_business_leave(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if the current user has an approved business leave today. Used by check-in page."""
    now_local = datetime.utcnow() + timedelta(hours=7)
    today = now_local.date()

    leave = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == current_user.id,
        LeaveRequest.leave_type == LeaveType.BUSINESS,
        LeaveRequest.status == LeaveStatus.APPROVED,
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today,
    ).first()

    if not leave:
        return {"has_leave": False}

    return {
        "has_leave": True,
        "start_time": _time_to_str(leave.leave_start_time),
        "end_time": _time_to_str(leave.leave_end_time),
    }
