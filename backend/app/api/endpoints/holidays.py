from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date as date_type, datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_gm_or_above
from app.models.holiday import Holiday
from app.models.user import User

router = APIRouter(prefix="/api/holidays", tags=["Holidays"])


class HolidayCreate(BaseModel):
    date: date_type
    name: str


class HolidayResponse(BaseModel):
    id: int
    date: date_type
    name: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[HolidayResponse])
def list_holidays(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all holidays, optionally filtered by year."""
    q = db.query(Holiday)
    if year:
        q = q.filter(
            Holiday.date >= date_type(year, 1, 1),
            Holiday.date <= date_type(year, 12, 31),
        )
    return q.order_by(Holiday.date).all()


@router.post("", response_model=HolidayResponse)
def create_holiday(
    body: HolidayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above),
):
    """Create a new holiday (admin only)."""
    existing = db.query(Holiday).filter(Holiday.date == body.date).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Holiday already exists on {body.date}")

    holiday = Holiday(date=body.date, name=body.name)
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


@router.delete("/{holiday_id}")
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above),
):
    """Delete a holiday (admin only)."""
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")

    db.delete(holiday)
    db.commit()
    return {"message": f"Holiday '{holiday.name}' deleted"}
