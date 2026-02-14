import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.reward import CoinLog
from app.api.deps import get_current_user, get_current_active_admin
from app.core.security import get_password_hash
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.schemas.reward import CoinLogResponse, CoinAdjustRequest

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/", response_model=UserResponse)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    # Create new user
    user_data = data.model_dump()
    if "password" in user_data:
        hashed_password = get_password_hash(user_data["password"])
        del user_data["password"]
        user_data["hashed_password"] = hashed_password
    
    user = User(**user_data)
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        # Check for integrity error (duplicate email)
        if "ix_users_email" in str(e):
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail=str(e))
    return user



@router.get("/", response_model=List[UserListResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if department:
        query = query.filter(User.department == department)
    users = query.offset(skip).limit(limit).all()
    return users


from app.api import deps

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_user)
):
    return current_user


class UpdateProfileRequest(BaseModel):
    phone: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.put("/me/profile", response_model=UserResponse)
def update_my_profile(
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Staff can update their own phone number."""
    if payload.phone is not None:
        current_user.phone = payload.phone
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/password")
def change_my_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Staff can change their own password."""
    from app.core.security import verify_password
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/me/upload-image", response_model=UserResponse)
def upload_my_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Staff can upload their own profile image."""
    ext = os.path.splitext(file.filename)[1]
    filename = f"user_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    upload_dir = os.path.join(settings.UPLOAD_DIR, "users")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    current_user.image = f"/uploads/users/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user

# ── Mana Rescue ──────────────────────────────────────

class RescueRequest(BaseModel):
    recipient_id: int


@router.get("/negative-coins")
def get_negative_coin_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users with negative coins (for Mana Rescue display)."""
    users = db.query(User).filter(
        User.coins < 0,
        User.id != current_user.id,
    ).order_by(User.coins.asc()).all()
    return [
        {
            "id": u.id,
            "name": f"{u.name} {u.surname or ''}".strip(),
            "image": u.image,
            "coins": u.coins,
            "position": u.position,
        }
        for u in users
    ]


@router.post("/rescue")
def rescue_user(
    req: RescueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Spend 1 Mana to give +5 Gold to a user with negative coins."""
    if current_user.id == req.recipient_id:
        raise HTTPException(status_code=400, detail="Cannot rescue yourself")

    if current_user.angel_coins < 1:
        raise HTTPException(status_code=400, detail="Insufficient Mana (need at least 1)")

    recipient = db.query(User).filter(User.id == req.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")

    if recipient.coins >= 0:
        raise HTTPException(status_code=400, detail="This user does not need rescuing (coins >= 0)")

    # Deduct 1 Mana from sender
    current_user.angel_coins -= 1

    # Give +5 Gold to recipient
    recipient.coins += 5

    sender_name = f"{current_user.name} {current_user.surname or ''}".strip()
    recipient_name = f"{recipient.name} {recipient.surname or ''}".strip()

    # Log for sender
    sender_log = CoinLog(
        user_id=current_user.id,
        amount=-1,
        reason=f"💖 Mana Rescue: sent to {recipient_name}",
        created_by="System",
    )
    db.add(sender_log)

    # Log for recipient (+5 Gold)
    recipient_log = CoinLog(
        user_id=recipient.id,
        amount=5,
        reason=f"💖 Mana Rescue from {sender_name}",
        created_by=sender_name,
    )
    db.add(recipient_log)

    db.commit()

    return {
        "message": f"Rescued {recipient_name}! +5 Gold",
        "sender_mana": current_user.angel_coins,
        "recipient_coins": recipient.coins,
        "recipient_name": recipient_name,
        "sender_name": sender_name,
    }


@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from app.models.approval import ApprovalFlow, ApprovalStep, ApprovalStepApprover
    from app.models.approval_pattern import ApprovalPatternStepApprover, ApprovalPatternStep, ApprovalPattern
    from app.models.attendance import Attendance
    from app.models.leave import LeaveRequest
    from app.models.reward import CoinLog, Redemption

    # Check if user is an approver in any approval flow
    approver_refs = db.query(ApprovalStepApprover).filter(
        ApprovalStepApprover.approver_id == user_id
    ).all()
    if approver_refs:
        step_ids = [ref.step_id for ref in approver_refs]
        steps = db.query(ApprovalStep).filter(ApprovalStep.id.in_(step_ids)).all()
        flow_ids = list({s.flow_id for s in steps})
        flows = db.query(ApprovalFlow).filter(ApprovalFlow.id.in_(flow_ids)).all()
        affected = []
        for f in flows:
            target = db.query(User).filter(User.id == f.target_user_id).first()
            affected.append({
                "user_id": f.target_user_id,
                "user_name": f"{target.name} {target.surname}" if target else "Unknown",
            })
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Cannot delete {user.name} {user.surname}: they are an approver in approval flows.",
                "affected_users": affected,
            },
        )

    # Check if user is in any approval patterns
    pattern_refs = db.query(ApprovalPatternStepApprover).filter(
        ApprovalPatternStepApprover.approver_id == user_id
    ).all()
    if pattern_refs:
        p_step_ids = [ref.step_id for ref in pattern_refs]
        p_steps = db.query(ApprovalPatternStep).filter(ApprovalPatternStep.id.in_(p_step_ids)).all()
        p_ids = list({s.pattern_id for s in p_steps})
        p_list = db.query(ApprovalPattern).filter(ApprovalPattern.id.in_(p_ids)).all()
        pattern_names = [{"pattern_id": p.id, "pattern_name": p.name} for p in p_list]
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Cannot delete {user.name} {user.surname}: they are used in approval patterns.",
                "affected_patterns": pattern_names,
            },
        )

    # Safe to delete — clean up related records
    db.query(ApprovalFlow).filter(ApprovalFlow.target_user_id == user_id).delete()
    db.query(Attendance).filter(Attendance.user_id == user_id).delete()
    db.query(LeaveRequest).filter(LeaveRequest.user_id == user_id).delete()
    db.query(CoinLog).filter(CoinLog.user_id == user_id).delete()
    db.query(Redemption).filter(Redemption.user_id == user_id).delete()

    db.delete(user)
    db.commit()
    return user


@router.post("/{user_id}/coins", response_model=UserResponse)
def adjust_user_coins(
    user_id: int,
    req: CoinAdjustRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.coins += req.amount
    
    log = CoinLog(
        user_id=user.id,
        amount=req.amount,
        reason=req.reason,
        created_by=f"{current_user.name} {current_user.surname}"
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/coin-logs", response_model=List[CoinLogResponse])
def get_user_coin_logs(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Allow user to see own logs, or admin to see anyone's
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    return db.query(CoinLog).filter(
        CoinLog.user_id == user_id,
        ~CoinLog.reason.like("%Angel%")
    ).order_by(CoinLog.created_at.desc()).all()


@router.get("/{user_id}/angel-coin-logs", response_model=List[CoinLogResponse])
def get_user_angel_coin_logs(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return only angel-coin-related log entries."""
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
         raise HTTPException(status_code=403, detail="Not authorized")
    return (
        db.query(CoinLog)
        .filter(CoinLog.user_id == user_id, CoinLog.reason.like("%Angel%"))
        .order_by(CoinLog.created_at.desc())
        .all()
    )


@router.get("/{user_id}/attendance")
def get_user_attendance(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    from app.models.attendance import Attendance
    return (
        db.query(Attendance)
        .filter(Attendance.user_id == user_id)
        .order_by(Attendance.timestamp.desc())
        .limit(50)
        .all()
    )


@router.get("/{user_id}/leaves")
def get_user_leaves(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    from app.models.leave import LeaveRequest
    return (
        db.query(LeaveRequest)
        .filter(LeaveRequest.user_id == user_id)
        .order_by(LeaveRequest.start_date.desc())
        .all()
    )


@router.get("/{user_id}/redemptions")
def get_user_redemptions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    from app.models.reward import Redemption
    return (
        db.query(Redemption)
        .filter(Redemption.user_id == user_id)
        .order_by(Redemption.created_at.desc())
        .all()
    )

@router.post("/{user_id}/image", response_model=UserResponse)
async def upload_user_image(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    upload_dir = os.path.join(settings.UPLOAD_DIR, "users")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    filename = f"user_{user_id}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user.image = f"/uploads/users/{filename}"
    db.commit()
    db.refresh(user)
    return user


@router.get("/departments/list", response_model=List[str])
def list_departments(db: Session = Depends(get_db)):
    departments = (
        db.query(User.department)
        .filter(User.department.isnot(None))
        .distinct()
        .all()
    )
    return [d[0] for d in departments]


# --- Angel Coins ---

class AngelCoinGrantRequest(BaseModel):
    amount: int
    reason: str = "Angel Coins granted"

class AngelCoinSendRequest(BaseModel):
    recipient_id: int
    amount: int
    comment: str = ""


@router.post("/{user_id}/angel-coins", response_model=UserResponse)
def grant_angel_coins(
    user_id: int,
    req: AngelCoinGrantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Admin grants angel coins to a user."""
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.angel_coins += req.amount
    
    log = CoinLog(
        user_id=user.id,
        amount=req.amount,  # Angel coins amount for the angel tab
        reason=f"🪽 Angel Coins +{req.amount}: {req.reason}",
        created_by=f"{current_user.name} {current_user.surname}"
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user


@router.post("/angel-coins/send")
def send_angel_coins(
    req: AngelCoinSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Staff sends angel coins to another staff. Converts to real coins for the receiver."""
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    if current_user.id == req.recipient_id:
        raise HTTPException(status_code=400, detail="Cannot send Angel Coins to yourself")
    
    if current_user.angel_coins < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient Angel Coins")
    
    recipient = db.query(User).filter(User.id == req.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # Deduct angel coins from sender
    current_user.angel_coins -= req.amount
    
    # Add real coins to recipient
    recipient.coins += req.amount
    
    comment_text = f": {req.comment}" if req.comment else ""
    
    # Log for sender (negative to show deduction)
    sender_log = CoinLog(
        user_id=current_user.id,
        amount=-req.amount,
        reason=f"🪽 Sent {req.amount} Angel Coins to {recipient.name} {recipient.surname}{comment_text}",
        created_by="System"
    )
    db.add(sender_log)
    
    # Log for recipient (real coins)
    recipient_log = CoinLog(
        user_id=recipient.id,
        amount=req.amount,
        reason=f"🪽 Received Angel Coins from {current_user.name} {current_user.surname}{comment_text}",
        created_by=f"{current_user.name} {current_user.surname}"
    )
    db.add(recipient_log)
    
    db.commit()
    
    return {
        "message": f"Sent {req.amount} Angel Coins to {recipient.name} {recipient.surname}",
        "sender_angel_coins": current_user.angel_coins,
        "recipient_coins": recipient.coins
    }


@router.get("/staff/list")
def get_staff_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all staff for angel coin recipient selection."""
    users = db.query(User).filter(
        User.id != current_user.id  # Exclude self
    ).all()
    return [
        {
            "id": u.id,
            "name": f"{u.name} {u.surname}",
            "department": u.department,
            "position": u.position,
            "image": u.image,
        }
        for u in users
    ]

