from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.work_request import WorkRequest, WorkRequestStatus
from app.models.attendance import Attendance
from app.models.user import User
from app.models.company import Company
from app.models.reward import CoinLog
from app.models.approval import ApprovalFlow, ApprovalStep, ApprovalStepApprover
from app.api.deps import get_current_user
from pydantic import BaseModel
import logging

logger = logging.getLogger("hr-api")

router = APIRouter(prefix="/api/work-requests", tags=["Work Requests"])


class WorkRequestResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    attendance_id: Optional[int] = None
    status: WorkRequestStatus
    created_at: Optional[datetime] = None
    check_in_time: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/pending-approvals", response_model=List[WorkRequestResponse])
def get_pending_work_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pending work requests from users that the current user can approve."""
    # Find all target_user_ids where current user is an approver
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

    requests = (
        db.query(WorkRequest)
        .filter(
            WorkRequest.user_id.in_(user_ids),
            WorkRequest.status == WorkRequestStatus.PENDING,
        )
        .order_by(WorkRequest.created_at.desc())
        .all()
    )

    result = []
    user_cache = {}
    for wr in requests:
        if wr.user_id not in user_cache:
            u = db.query(User).filter(User.id == wr.user_id).first()
            user_cache[wr.user_id] = f"{u.name} {u.surname}" if u else "Unknown"

        # Get check-in time from attendance
        check_in_time = None
        if wr.attendance_id:
            att = db.query(Attendance).filter(Attendance.id == wr.attendance_id).first()
            if att:
                local_ts = att.timestamp + timedelta(hours=7)
                check_in_time = local_ts.strftime("%d %b %Y %H:%M")

        result.append(
            WorkRequestResponse(
                id=wr.id,
                user_id=wr.user_id,
                user_name=user_cache[wr.user_id],
                attendance_id=wr.attendance_id,
                status=wr.status,
                created_at=wr.created_at,
                check_in_time=check_in_time,
            )
        )
    return result


@router.put("/{request_id}/approve")
def approve_work_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a work request. Grants coins based on actual check-in time."""
    wr = db.query(WorkRequest).filter(WorkRequest.id == request_id).first()
    if not wr:
        raise HTTPException(status_code=404, detail="Work request not found")
    if wr.status != WorkRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Already {wr.status.value}")

    wr.status = WorkRequestStatus.APPROVED

    user = db.query(User).filter(User.id == wr.user_id).first()
    company = db.query(Company).first()

    # Get the original attendance record to determine check-in time
    attendance = db.query(Attendance).filter(Attendance.id == wr.attendance_id).first() if wr.attendance_id else None

    coin_change = 0
    coin_reason = ""
    status = "present"

    if attendance:
        # Use original check-in timestamp to determine on-time / late / absent
        checkin_local = attendance.timestamp + timedelta(hours=7)
        checkin_time = checkin_local.time()

        from datetime import time as dt_time
        start = user.work_start_time or dt_time(9, 0)
        start_minutes = start.hour * 60 + start.minute
        checkin_minutes = checkin_time.hour * 60 + checkin_time.minute
        diff = checkin_minutes - start_minutes

        if diff > 60:
            status = "absent"
        elif diff > 0:
            status = "late"

        # Update attendance status
        attendance.status = status

        # Coin logic
        if company:
            if status == "absent":
                if company.coin_absent_penalty:
                    coin_change = -company.coin_absent_penalty
                    coin_reason = "Absent (remote request approved, >1hr late)"
            elif status == "late":
                if company.coin_late_penalty:
                    coin_change = -company.coin_late_penalty
                    coin_reason = "Late (remote request approved)"
            else:
                if company.coin_on_time:
                    coin_change = company.coin_on_time
                    coin_reason = "On-time (remote request approved)"
    else:
        # No attendance record — just grant on-time coins
        if company and company.coin_on_time:
            coin_change = company.coin_on_time
            coin_reason = "Work Request approved"

    if coin_change != 0 and user:
        user.coins += coin_change
        log = CoinLog(
            user_id=user.id,
            amount=coin_change,
            reason=coin_reason,
            created_by=f"{current_user.name} {current_user.surname}",
        )
        db.add(log)

    db.commit()

    logger.info(f"✅ Work Request #{request_id} approved for {user.name} {user.surname} (status={status}, coins={coin_change})")
    return {
        "message": f"Work Request approved ({status}). {user.name} received {coin_change} coins.",
        "coin_change": coin_change,
        "status": status,
    }


@router.put("/{request_id}/reject")
def reject_work_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a work request. Employee can still GPS check-in."""
    wr = db.query(WorkRequest).filter(WorkRequest.id == request_id).first()
    if not wr:
        raise HTTPException(status_code=404, detail="Work request not found")
    if wr.status != WorkRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Already {wr.status.value}")

    wr.status = WorkRequestStatus.REJECTED

    # Mark the attendance record as 'rejected' so it's not counted as a valid check-in
    # but also doesn't block a new GPS check-in
    if wr.attendance_id:
        attendance = db.query(Attendance).filter(Attendance.id == wr.attendance_id).first()
        if attendance:
            attendance.status = "rejected"

    db.commit()

    logger.info(f"❌ Work Request #{request_id} rejected — employee can still GPS check-in")
    return {"message": "Work Request rejected. Employee can still check in via GPS."}
