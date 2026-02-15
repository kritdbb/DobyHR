import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_gm_or_above
from app.models.user import User
from app.models.fortune_wheel import FortuneWheel
from app.models.reward import CoinLog
from app.schemas.fortune_wheel import (
    FortuneWheelCreate, FortuneWheelUpdate, FortuneWheelResponse,
    SpinResult, WheelSegment,
)

router = APIRouter(prefix="/api/fortune-wheels", tags=["Fortune Wheels"])


# ── Admin CRUD ─────────────────────────────────────────────

@router.get("/", response_model=List[FortuneWheelResponse])
def list_wheels(db: Session = Depends(get_db), current_user: User = Depends(get_current_gm_or_above)):
    return db.query(FortuneWheel).order_by(FortuneWheel.id.desc()).all()


@router.post("/", response_model=FortuneWheelResponse)
def create_wheel(payload: FortuneWheelCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_gm_or_above)):
    wheel = FortuneWheel(
        name=payload.name,
        segments=[s.model_dump() for s in payload.segments],
        spin_min=payload.spin_min,
        spin_max=payload.spin_max,
        currency=payload.currency,
        price=payload.price,
        is_active=payload.is_active,
    )
    db.add(wheel)
    db.commit()
    db.refresh(wheel)
    return wheel


@router.put("/{wheel_id}", response_model=FortuneWheelResponse)
def update_wheel(wheel_id: int, payload: FortuneWheelUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_gm_or_above)):
    wheel = db.query(FortuneWheel).filter(FortuneWheel.id == wheel_id).first()
    if not wheel:
        raise HTTPException(status_code=404, detail="Wheel not found")
    update_data = payload.model_dump(exclude_unset=True)
    if "segments" in update_data and update_data["segments"] is not None:
        update_data["segments"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in update_data["segments"]]
    for k, v in update_data.items():
        setattr(wheel, k, v)
    db.commit()
    db.refresh(wheel)
    return wheel


@router.delete("/{wheel_id}")
def delete_wheel(wheel_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_gm_or_above)):
    wheel = db.query(FortuneWheel).filter(FortuneWheel.id == wheel_id).first()
    if not wheel:
        raise HTTPException(status_code=404, detail="Wheel not found")
    db.delete(wheel)
    db.commit()
    return {"ok": True}


# ── Staff: list active wheels ──────────────────────────────

@router.get("/active", response_model=List[FortuneWheelResponse])
def list_active_wheels(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(FortuneWheel).filter(FortuneWheel.is_active == True).all()


# ── Staff: spin a wheel ───────────────────────────────────

@router.post("/{wheel_id}/spin", response_model=SpinResult)
def spin_wheel(wheel_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wheel = db.query(FortuneWheel).filter(FortuneWheel.id == wheel_id, FortuneWheel.is_active == True).first()
    if not wheel:
        raise HTTPException(status_code=404, detail="Wheel not found or inactive")

    # Check user balance
    user = db.query(User).filter(User.id == current_user.id).first()
    if wheel.currency == "gold":
        if user.coins < wheel.price:
            raise HTTPException(status_code=400, detail=f"Not enough Gold. Need {wheel.price}, have {user.coins}")
    elif wheel.currency == "mana":
        if user.angel_coins < wheel.price:
            raise HTTPException(status_code=400, detail=f"Not enough Mana. Need {wheel.price}, have {user.angel_coins}")

    # Deduct cost
    if wheel.currency == "gold":
        user.coins -= wheel.price
        db.add(CoinLog(user_id=user.id, amount=-wheel.price, reason=f"Fortune Wheel: {wheel.name}", created_by="System"))
    else:
        user.angel_coins -= wheel.price

    # Weighted random pick
    segments = wheel.segments
    total = sum(s.get("weight", 1) for s in segments)
    rand = random.random() * total
    winner_index = 0
    for i, s in enumerate(segments):
        rand -= s.get("weight", 1)
        if rand <= 0:
            winner_index = i
            break

    seg = segments[winner_index]
    reward_type = seg.get("reward_type", "nothing")
    reward_amount = seg.get("reward_amount", 0)

    # Apply reward
    message = f"🎡 {seg.get('label', 'Unknown')}"
    if reward_type == "gold" and reward_amount > 0:
        user.coins += reward_amount
        db.add(CoinLog(user_id=user.id, amount=reward_amount, reason=f"Fortune Wheel Prize: {seg.get('label', '')}", created_by="System"))
        message = f"💰 Won {reward_amount} Gold!"
    elif reward_type == "mana" and reward_amount > 0:
        user.angel_coins += reward_amount
        message = f"✨ Won {reward_amount} Mana!"
    elif reward_type == "str" and reward_amount > 0:
        user.base_str = (user.base_str or 1) + reward_amount
        message = f"⚔️ STR +{reward_amount}!"
    elif reward_type == "def" and reward_amount > 0:
        user.base_def = (user.base_def or 1) + reward_amount
        message = f"🛡️ DEF +{reward_amount}!"
    elif reward_type == "luk" and reward_amount > 0:
        user.base_luk = (user.base_luk or 1) + reward_amount
        message = f"🍀 LUK +{reward_amount}!"
    else:
        message = f"😅 {seg.get('label', 'Nothing')} — Better luck next time!"

    # Determine spin rotations
    rotations = random.randint(wheel.spin_min, wheel.spin_max)

    db.commit()
    return SpinResult(
        segment_index=winner_index,
        segment=WheelSegment(**seg),
        rotations=rotations,
        message=message,
        coins=user.coins,
        angel_coins=user.angel_coins,
    )
