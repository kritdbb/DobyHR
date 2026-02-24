"""
Location CRUD endpoints for multi-branch check-in.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_gm_or_above
from app.models.location import Location

router = APIRouter(prefix="/api/locations", tags=["Locations"])


# ── Schemas ──────────────────────────────────────────────

class LocationCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    radius: int = 200
    is_active: bool = True


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[int] = None
    is_active: Optional[bool] = None


class LocationResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    radius: int
    is_active: bool

    class Config:
        from_attributes = True


# ── Endpoints ────────────────────────────────────────────

@router.get("/", response_model=List[LocationResponse])
def list_locations(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """List all locations (any authenticated user)."""
    return db.query(Location).order_by(Location.id).all()


@router.post("/", response_model=LocationResponse)
def create_location(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_gm_or_above),
):
    loc = Location(
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius=payload.radius,
        is_active=payload.is_active,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    payload: LocationUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_gm_or_above),
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(loc, k, v)
    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/{location_id}")
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_gm_or_above),
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    db.delete(loc)
    db.commit()
    return {"ok": True}
