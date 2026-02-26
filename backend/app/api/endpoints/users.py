import os
import uuid
import shutil
from datetime import timedelta
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.reward import CoinLog
from app.api.deps import get_current_user, get_current_gm_or_above
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
    from app.utils.image_compress import compress_and_save
    upload_dir = os.path.join(settings.UPLOAD_DIR, "users")
    base_name = f"user_{current_user.id}_{uuid.uuid4().hex[:8]}"
    filename = compress_and_save(file.file, upload_dir, base_name)
    current_user.image = f"/uploads/users/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/background")
def upload_magic_background(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Upload a custom card background image. Costs 2 Mana per upload."""
    MANA_COST = 2
    if (current_user.angel_coins or 0) < MANA_COST:
        raise HTTPException(status_code=400, detail=f"Not enough Mana! Need {MANA_COST}")

    ext = os.path.splitext(file.filename)[1]
    filename = f"bg_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    upload_dir = os.path.join(settings.UPLOAD_DIR, "backgrounds")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    current_user.angel_coins -= MANA_COST
    current_user.magic_background = f"/uploads/backgrounds/{filename}"
    db.commit()
    return {
        "item": "Magic Background",
        "magic_background": current_user.magic_background,
        "angel_coins": current_user.angel_coins,
    }

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
    """Revival Pool: contribute Mana to help revive a dead user. Requires multiple people."""
    from app.models.company import Company

    if current_user.id == req.recipient_id:
        raise HTTPException(status_code=400, detail="Cannot rescue yourself")

    recipient = db.query(User).filter(User.id == req.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")

    if (recipient.coins or 0) >= 0:
        raise HTTPException(status_code=400, detail="This user does not need rescuing (coins >= 0)")

    # Get rescue config
    company = db.query(Company).first()
    cost = (company.rescue_cost_per_person if company else 1) or 1
    required = (company.rescue_required_people if company else 3) or 3
    gold_on_revive = (company.rescue_gold_on_revive if company else 0) or 0

    if (current_user.angel_coins or 0) < cost:
        raise HTTPException(status_code=400, detail=f"Insufficient Mana (need {cost})")

    # Check if this user already contributed to this revival
    existing_prayer = db.query(CoinLog).filter(
        CoinLog.user_id == recipient.id,
        CoinLog.reason.ilike(f"%Revival Prayer from {current_user.name}%"),
        CoinLog.amount == 0,
    ).first()
    if existing_prayer:
        raise HTTPException(status_code=400, detail="You already contributed to this revival!")

    sender_name = f"{current_user.name} {current_user.surname or ''}".strip()
    recipient_name = f"{recipient.name} {recipient.surname or ''}".strip()

    # Deduct Mana from sender
    current_user.angel_coins -= cost

    # Log sender's contribution
    sender_log = CoinLog(
        user_id=current_user.id,
        amount=-cost,
        reason=f"🙏 Revival Contribution for {recipient_name}",
        created_by="System",
        sender_user_id=current_user.id,
    )
    db.add(sender_log)

    # Log prayer on recipient (amount=0, used for counting)
    prayer_log = CoinLog(
        user_id=recipient.id,
        amount=0,
        reason=f"🙏 Revival Prayer from {sender_name}",
        created_by=sender_name,
        sender_user_id=current_user.id,
    )
    db.add(prayer_log)
    db.flush()

    # Count current prayers for this recipient
    prayer_count = db.query(CoinLog).filter(
        CoinLog.user_id == recipient.id,
        CoinLog.reason.ilike("🙏 Revival Prayer from%"),
        CoinLog.amount == 0,
    ).count()

    revived = False
    if prayer_count >= required:
        # REVIVE! Set coins to configured amount
        recipient.coins = gold_on_revive

        # Gather all rescuer names
        prayer_logs = db.query(CoinLog).filter(
            CoinLog.user_id == recipient.id,
            CoinLog.reason.ilike("🙏 Revival Prayer from%"),
            CoinLog.amount == 0,
        ).all()
        rescuer_names = [p.created_by for p in prayer_logs]

        # Delete prayer logs (cleanup)
        for p in prayer_logs:
            db.delete(p)

        # Create revival celebration log
        revival_log = CoinLog(
            user_id=recipient.id,
            amount=gold_on_revive,
            reason=f"💖 Revived by {', '.join(rescuer_names)}!",
            created_by="Revival Pool",
        )
        db.add(revival_log)
        revived = True

    db.commit()

    if revived:
        return {
            "message": f"🎉 {recipient_name} has been REVIVED!",
            "revived": True,
            "prayer_count": required,
            "required": required,
            "rescuers": rescuer_names,
            "recipient_coins": recipient.coins,
            "sender_mana": current_user.angel_coins,
        }
    else:
        return {
            "message": f"🙏 Prayer sent! {prayer_count}/{required} needed to revive {recipient_name}",
            "revived": False,
            "prayer_count": prayer_count,
            "required": required,
            "recipient_name": recipient_name,
            "sender_mana": current_user.angel_coins,
        }


@router.get("/rescue/records")
def get_revival_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get revival history for the Hall of Fame."""
    logs = db.query(CoinLog).filter(
        CoinLog.reason.ilike("💖 Revived by%"),
    ).order_by(CoinLog.created_at.desc()).limit(50).all()

    records = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        # Parse rescuer names from reason: "💖 Revived by Name1, Name2!"
        rescuers_str = log.reason.replace("💖 Revived by ", "").rstrip("!")
        rescuer_names = [n.strip() for n in rescuers_str.split(",")]

        # Look up rescuer images
        rescuers = []
        for rname in rescuer_names:
            # Match by first name
            rescuer = db.query(User).filter(User.name == rname.split()[0] if rname else "").first()
            rescuers.append({
                "name": rname,
                "image": rescuer.image if rescuer else None,
            })

        records.append({
            "id": log.id,
            "revived_user": {
                "id": user.id if user else None,
                "name": f"{user.name} {user.surname or ''}".strip() if user else "Unknown",
                "image": user.image if user else None,
            },
            "rescuers": rescuers,
            "rescuer_count": len(rescuer_names),
            "gold_given": log.amount,
            "date": log.created_at.isoformat() if log.created_at else None,
        })

    return records


@router.get("/rescue/pool/{user_id}")
def get_rescue_pool(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current revival pool status for a dead user."""
    from app.models.company import Company

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    company = db.query(Company).first()
    required = (company.rescue_required_people if company else 3) or 3
    cost = (company.rescue_cost_per_person if company else 1) or 1

    if (user.coins or 0) >= 0:
        return {"is_dead": False, "prayer_count": 0, "required": required, "contributors": [], "cost": cost}

    prayers = db.query(CoinLog).filter(
        CoinLog.user_id == user_id,
        CoinLog.reason.ilike("🙏 Revival Prayer from%"),
        CoinLog.amount == 0,
    ).all()

    contributors = [p.created_by for p in prayers]
    already_contributed = any(
        current_user.name in c for c in contributors
    )

    return {
        "is_dead": True,
        "prayer_count": len(prayers),
        "required": required,
        "cost": cost,
        "contributors": contributors,
        "already_contributed": already_contributed,
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
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above)
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
    current_user: User = Depends(get_current_gm_or_above)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.coins += req.amount
    
    log = CoinLog(
        user_id=user.id,
        amount=req.amount,
        reason=req.reason,
        created_by=f"{current_user.name} {current_user.surname}",
        sender_user_id=current_user.id,
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/coin-logs")
def get_user_coin_logs(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Allow user to see own logs, or admin to see anyone's
    if current_user.id != user_id and current_user.role not in (UserRole.GOD, UserRole.GM):
         raise HTTPException(status_code=403, detail="Not authorized")
         
    logs = db.query(CoinLog).filter(
        CoinLog.user_id == user_id,
        ~CoinLog.reason.like("%Angel%")
    ).order_by(CoinLog.created_at.desc()).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "amount": log.amount,
            "reason": log.reason,
            "created_by": log.created_by,
            "created_at": (log.created_at + timedelta(hours=7)).isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/{user_id}/angel-coin-logs")
def get_user_angel_coin_logs(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return only angel-coin-related log entries."""
    if current_user.id != user_id and current_user.role not in (UserRole.GOD, UserRole.GM):
         raise HTTPException(status_code=403, detail="Not authorized")

    logs = (
        db.query(CoinLog)
        .filter(CoinLog.user_id == user_id, CoinLog.reason.like("%Angel%"))
        .order_by(CoinLog.created_at.desc())
        .all()
    )

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "amount": log.amount,
            "reason": log.reason,
            "created_by": log.created_by,
            "created_at": (log.created_at + timedelta(hours=7)).isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/{user_id}/attendance")
def get_user_attendance(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above),
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
    current_user: User = Depends(get_current_gm_or_above),
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
    current_user: User = Depends(get_current_gm_or_above),
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

    from app.utils.image_compress import compress_and_save
    upload_dir = os.path.join(settings.UPLOAD_DIR, "users")
    base_name = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
    filename = compress_and_save(file.file, upload_dir, base_name)

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
    delivery_type: str = "gold"  # "gold" or "mana"


@router.post("/{user_id}/angel-coins", response_model=UserResponse)
def grant_angel_coins(
    user_id: int,
    req: AngelCoinGrantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above)
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
    """Staff sends mana to another staff. Delivery as gold or mana (1:1)."""
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    if req.delivery_type not in ("gold", "mana"):
        raise HTTPException(status_code=400, detail="delivery_type must be 'gold' or 'mana'")
    
    if current_user.id == req.recipient_id:
        raise HTTPException(status_code=400, detail="Cannot send Mana to yourself")
    
    if (current_user.angel_coins or 0) < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient Mana")
    
    recipient = db.query(User).filter(User.id == req.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # Deduct mana from sender
    current_user.angel_coins = (current_user.angel_coins or 0) - req.amount
    
    # Deliver to recipient as gold or mana
    delivery_label = "Gold" if req.delivery_type == "gold" else "Mana"
    if req.delivery_type == "gold":
        recipient.coins = (recipient.coins or 0) + req.amount
    else:
        recipient.angel_coins = (recipient.angel_coins or 0) + req.amount
    
    comment_text = f": {req.comment}" if req.comment else ""
    
    # Log for sender (negative — mana deduction)
    sender_log = CoinLog(
        user_id=current_user.id,
        amount=-req.amount,
        reason=f"🪽 Sent {req.amount} Mana as {delivery_label} to {recipient.name} {recipient.surname}{comment_text}",
        log_type="mana_gift",
        created_by="System",
        sender_user_id=current_user.id,
    )
    db.add(sender_log)
    
    # Log for recipient
    recipient_log = CoinLog(
        user_id=recipient.id,
        amount=req.amount,
        reason=f"🪽 Received {delivery_label} from {current_user.name} {current_user.surname}{comment_text}",
        log_type="mana_gift",
        created_by=f"{current_user.name} {current_user.surname}",
        sender_user_id=current_user.id,
    )
    db.add(recipient_log)
    
    db.commit()

    # Webhook: mana gift
    from app.services.notifications import send_town_crier_webhook
    sender_name = f"{current_user.name} {current_user.surname or ''}".strip()
    rcpt_name = f"{recipient.name} {recipient.surname or ''}".strip()
    send_town_crier_webhook(f"✨ *{sender_name}* gifted {req.amount} {delivery_label} to *{rcpt_name}*{comment_text}")

    return {
        "message": f"Sent {req.amount} Mana as {delivery_label} to {recipient.name} {recipient.surname}",
        "sender_mana": current_user.angel_coins,
        "delivery_type": req.delivery_type,
        "recipient_coins": recipient.coins,
        "recipient_mana": recipient.angel_coins,
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


# ═══════ Face Image Endpoints ═══════

from app.models.face_image import UserFaceImage

@router.get("/{user_id}/face-images")
def get_user_face_images(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all face images for a user."""
    images = db.query(UserFaceImage).filter(UserFaceImage.user_id == user_id).all()
    return [
        {
            "id": img.id,
            "user_id": img.user_id,
            "image_path": img.image_path,
            "created_at": img.created_at,
        }
        for img in images
    ]


@router.post("/{user_id}/face-images")
def upload_user_face_image(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above)
):
    """Upload a face image for a user (max 2). Triggers FAISS index rebuild."""
    # Check user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check max 2 face images
    existing_count = db.query(UserFaceImage).filter(UserFaceImage.user_id == user_id).count()
    if existing_count >= 2:
        raise HTTPException(status_code=400, detail="Maximum 2 face images allowed. Delete an existing one first.")

    # Save file
    ext = os.path.splitext(file.filename)[1]
    filename = f"face_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
    upload_dir = os.path.join(settings.UPLOAD_DIR, "face_images")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    face_img = UserFaceImage(
        user_id=user_id,
        image_path=f"/uploads/face_images/{filename}",
    )
    db.add(face_img)
    db.commit()
    db.refresh(face_img)

    # Trigger FAISS rebuild in background
    _trigger_faiss_rebuild()

    return {
        "id": face_img.id,
        "user_id": face_img.user_id,
        "image_path": face_img.image_path,
        "created_at": face_img.created_at,
    }


@router.delete("/{user_id}/face-images/{image_id}")
def delete_user_face_image(
    user_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above)
):
    """Delete a face image. Triggers FAISS index rebuild."""
    face_img = db.query(UserFaceImage).filter(
        UserFaceImage.id == image_id,
        UserFaceImage.user_id == user_id
    ).first()
    if not face_img:
        raise HTTPException(status_code=404, detail="Face image not found")

    # Delete file from disk
    full_path = os.path.join(settings.UPLOAD_DIR, face_img.image_path.lstrip("/uploads/"))
    if os.path.exists(full_path):
        os.remove(full_path)

    db.delete(face_img)
    db.commit()

    # Trigger FAISS rebuild in background
    _trigger_faiss_rebuild()

    return {"message": "Face image deleted"}


def _trigger_faiss_rebuild():
    """Trigger FAISS index rebuild in a background thread."""
    import threading
    import logging
    logger = logging.getLogger("hr-api")
    def _rebuild():
        try:
            from app.services.face_service import rebuild_index
            rebuild_index()
        except Exception as e:
            logger.error(f"❌ FAISS rebuild failed: {e}")
    threading.Thread(target=_rebuild, daemon=True).start()
    logger.info("🔄 FAISS rebuild triggered in background")
