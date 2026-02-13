import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.company import Company
from app.schemas.company import CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/api/company", tags=["company"])


@router.get("/", response_model=CompanyResponse)
def get_company(db: Session = Depends(get_db)):
    company = db.query(Company).first()
    if not company:
        # Create default company if none exists
        company = Company(name="My Company")
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


@router.put("/", response_model=CompanyResponse)
def update_company(data: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.query(Company).first()
    if not company:
        company = Company(name="My Company")
        db.add(company)
        db.commit()
        db.refresh(company)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return company


@router.post("/logo", response_model=CompanyResponse)
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    company = db.query(Company).first()
    if not company:
        company = Company(name="My Company")
        db.add(company)
        db.commit()
        db.refresh(company)

    # Ensure upload directory exists
    upload_dir = os.path.join(settings.UPLOAD_DIR, "company")
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    filename = f"logo_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    company.logo = f"/uploads/company/{filename}"
    db.commit()
    db.refresh(company)
    return company
