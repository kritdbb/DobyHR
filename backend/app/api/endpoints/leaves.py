from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List, Optional
from app.core.database import get_db
from app.models.leave import LeaveRequest, LeaveType, LeaveStatus
from app.models.user import User
from app.models.attendance import Attendance
from app.models.company import Company
from app.models.reward import CoinLog
from app.models.approval import ApprovalFlow, ApprovalStep, ApprovalStepApprover
from app.api.deps import get_current_user, get_current_active_admin
from pydantic import BaseModel
import logging

logger = logging.getLogger("hr-api")

router = APIRouter(prefix="/api/leaves", tags=["Leaves"])

class LeaveRequestCreate(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str

class LeaveRequestResponse(BaseModel):
    id: int
    user_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatus

    class Config:
        from_attributes = True

@router.post("/request", response_model=LeaveRequestResponse)
def request_leave(
    req: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Validation
    if req.end_date < req.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    duration = (req.end_date - req.start_date).days + 1
    
    # 2. Check Quota
    used_days = 0
    past_leaves = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == current_user.id,
        LeaveRequest.leave_type == req.leave_type,
        LeaveRequest.status != LeaveStatus.REJECTED
    ).all()
    
    for leave in past_leaves:
        days = (leave.end_date - leave.start_date).days + 1
        used_days += days
        
    quota = 0
    if req.leave_type == LeaveType.SICK:
        quota = current_user.sick_leave_days
    elif req.leave_type == LeaveType.BUSINESS:
        quota = current_user.business_leave_days
    elif req.leave_type == LeaveType.VACATION:
        quota = current_user.vacation_leave_days
        
    if used_days + duration > quota:
        raise HTTPException(status_code=400, detail=f"Insufficient leave quota. Remaining: {quota - used_days}, Requested: {duration}")

    # 3. Create Request
    leave_request = LeaveRequest(
        user_id=current_user.id,
        leave_type=req.leave_type,
        start_date=req.start_date,
        end_date=req.end_date,
        reason=req.reason,
        status=LeaveStatus.PENDING
    )
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request

@router.get("/my-leaves", response_model=List[LeaveRequestResponse])
def get_my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id).order_by(LeaveRequest.start_date.desc()).all()

@router.get("/quota")
def get_leave_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    def count_used(l_type):
        leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == current_user.id,
            LeaveRequest.leave_type == l_type,
            LeaveRequest.status != LeaveStatus.REJECTED
        ).all()
        return sum([(l.end_date - l.start_date).days + 1 for l in leaves])

    return {
        "sick": {"total": current_user.sick_leave_days, "used": count_used(LeaveType.SICK)},
        "business": {"total": current_user.business_leave_days, "used": count_used(LeaveType.BUSINESS)},
        "vacation": {"total": current_user.vacation_leave_days, "used": count_used(LeaveType.VACATION)},
    }

@router.get("/all", response_model=List[LeaveRequestResponse])
def get_all_leaves(
    status: LeaveStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    query = db.query(LeaveRequest).order_by(LeaveRequest.start_date.desc())
    if status:
        query = query.filter(LeaveRequest.status == status)
    return query.all()


@router.put("/{leave_id}/approve", response_model=LeaveRequestResponse)
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
    
    leave.status = LeaveStatus.APPROVED

    # ── Sick Leave Coin Refund ──────────────────────────────
    # If sick leave: check if user was penalized (absent penalty) for leave dates → refund
    if leave.leave_type == LeaveType.SICK:
        user = db.query(User).filter(User.id == leave.user_id).first()
        total_refund = 0

        current_date = leave.start_date
        while current_date <= leave.end_date:
            date_str = current_date.isoformat()
            
            # Check for absent_check penalty (reason like "Absent penalty (YYYY-MM-DD)")
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
    return leave


@router.put("/{leave_id}/reject", response_model=LeaveRequestResponse)
def reject_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot reject a leave that is already {leave.status.value}")
    
    leave.status = LeaveStatus.REJECTED
    db.commit()
    db.refresh(leave)
    return leave


class PendingLeaveApprovalResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatus

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
            )
        )
    return result
