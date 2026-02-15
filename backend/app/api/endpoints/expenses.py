from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date, datetime
import os, uuid, shutil

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user, get_current_gm_or_above
from app.models.user import User
from app.models.expense import (
    ExpenseRequest, ExpenseAttachment,
    ExpenseType, ExpenseStatus, VehicleType,
)
from app.models.approval import ApprovalFlow, ApprovalStep, ApprovalStepApprover
from pydantic import BaseModel

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])

RATE_CAR = 10       # baht per km
RATE_MOTORCYCLE = 5  # baht per km


# ───────── helpers ─────────

def _save_file(upload: UploadFile, subfolder: str = "expenses") -> str:
    """Save uploaded file and return its URL path."""
    dest_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(dest_dir, exist_ok=True)
    ext = os.path.splitext(upload.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(dest_dir, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return f"/uploads/{subfolder}/{filename}"


def _expense_to_dict(exp: ExpenseRequest) -> dict:
    """Convert an ExpenseRequest ORM object to a response dict."""
    user = exp.user
    d = {
        "id": exp.id,
        "user_id": exp.user_id,
        "user_name": f"{user.name} {user.surname}" if user else "Unknown",
        "expense_type": exp.expense_type.value if exp.expense_type else None,
        "status": exp.status.value if exp.status else None,
        "created_at": exp.created_at.isoformat() if exp.created_at else None,
        "current_step": exp.current_step,
        "total_steps": exp.total_steps,
        # General
        "expense_date": exp.expense_date.isoformat() if exp.expense_date else None,
        "description": exp.description,
        "amount": exp.amount,
        "file_path": exp.file_path,
        # Travel
        "travel_date": exp.travel_date.isoformat() if exp.travel_date else None,
        "vehicle_type": exp.vehicle_type.value if exp.vehicle_type else None,
        "km_outbound": exp.km_outbound,
        "km_return": exp.km_return,
        "travel_cost": exp.travel_cost,
        "other_cost": exp.other_cost,
        "total_amount": exp.total_amount,
        "outbound_image": exp.outbound_image,
        "return_image": exp.return_image,
        "attachments": [{"id": a.id, "file_path": a.file_path} for a in (exp.attachments or [])],
    }
    return d


def _get_user_total_steps(user_id: int, db: Session) -> int:
    """Get the total number of approval steps for a user."""
    flow = db.query(ApprovalFlow).filter(ApprovalFlow.target_user_id == user_id).first()
    if not flow:
        return 0
    return len(flow.steps)


# ───────── CREATE GENERAL EXPENSE ─────────

@router.post("/general")
async def create_general_expense(
    expense_date: str = Form(...),
    description: str = Form(...),
    amount: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_url = _save_file(file)
    total_steps = _get_user_total_steps(current_user.id, db)

    exp = ExpenseRequest(
        user_id=current_user.id,
        expense_type=ExpenseType.GENERAL,
        expense_date=date.fromisoformat(expense_date),
        description=description,
        amount=amount,
        file_path=file_url,
        total_steps=total_steps,
        current_step=0,
        status=ExpenseStatus.PENDING if total_steps > 0 else ExpenseStatus.ALL_APPROVED,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return _expense_to_dict(exp)

# ───────── CREATE CENTER EXPENSE ─────────
# Like general but: owner = admin@admin.com, auto-approved

@router.post("/center")
async def create_center_expense(
    expense_date: str = Form(...),
    description: str = Form(...),
    amount: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_user = db.query(User).filter(User.email == "admin@admin.com").first()
    if not admin_user:
        raise HTTPException(status_code=400, detail="admin@admin.com user not found")

    file_url = _save_file(file)

    exp = ExpenseRequest(
        user_id=admin_user.id,
        expense_type=ExpenseType.CENTER,
        expense_date=date.fromisoformat(expense_date),
        description=description,
        amount=amount,
        file_path=file_url,
        total_steps=0,
        current_step=0,
        status=ExpenseStatus.ALL_APPROVED,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return _expense_to_dict(exp)


# ───────── CREATE TRAVEL EXPENSE ─────────

@router.post("/travel")
async def create_travel_expense(
    travel_date: str = Form(...),
    vehicle_type: str = Form(...),
    km_outbound: float = Form(...),
    km_return: float = Form(...),
    description: str = Form(""),
    other_cost: float = Form(0),
    outbound_image: UploadFile = File(...),
    return_image: UploadFile = File(...),
    other_files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vt = VehicleType(vehicle_type.upper())
    rate = RATE_CAR if vt == VehicleType.CAR else RATE_MOTORCYCLE
    travel_cost = (km_outbound + km_return) * rate
    total_amount = travel_cost + other_cost

    outbound_url = _save_file(outbound_image)
    return_url = _save_file(return_image)

    total_steps = _get_user_total_steps(current_user.id, db)

    exp = ExpenseRequest(
        user_id=current_user.id,
        expense_type=ExpenseType.TRAVEL,
        travel_date=date.fromisoformat(travel_date),
        description=description or None,
        vehicle_type=vt,
        km_outbound=km_outbound,
        km_return=km_return,
        travel_cost=travel_cost,
        other_cost=other_cost,
        total_amount=total_amount,
        amount=total_amount,
        outbound_image=outbound_url,
        return_image=return_url,
        total_steps=total_steps,
        current_step=0,
        status=ExpenseStatus.PENDING if total_steps > 0 else ExpenseStatus.ALL_APPROVED,
    )
    db.add(exp)
    db.flush()

    # Save other cost attachments
    for f in other_files:
        if f.filename:
            url = _save_file(f)
            db.add(ExpenseAttachment(expense_id=exp.id, file_path=url))

    db.commit()
    db.refresh(exp)
    return _expense_to_dict(exp)


# ───────── MY EXPENSES ─────────

@router.get("/my")
def get_my_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exps = (
        db.query(ExpenseRequest)
        .options(joinedload(ExpenseRequest.attachments), joinedload(ExpenseRequest.user))
        .filter(ExpenseRequest.user_id == current_user.id)
        .order_by(ExpenseRequest.created_at.desc())
        .all()
    )
    return [_expense_to_dict(e) for e in exps]


# ───────── PENDING APPROVALS (for approval board) ─────────

@router.get("/pending-approvals")
def get_pending_expense_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pending expenses from users that current_user is an approver for."""
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

    exps = (
        db.query(ExpenseRequest)
        .options(joinedload(ExpenseRequest.attachments), joinedload(ExpenseRequest.user))
        .filter(
            ExpenseRequest.user_id.in_(user_ids),
            ExpenseRequest.status == ExpenseStatus.PENDING,
        )
        .order_by(ExpenseRequest.created_at.desc())
        .all()
    )
    return [_expense_to_dict(e) for e in exps]


# ───────── APPROVE / REJECT (approval board) ─────────

@router.put("/{expense_id}/approve")
def approve_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = db.query(ExpenseRequest).options(
        joinedload(ExpenseRequest.attachments), joinedload(ExpenseRequest.user)
    ).filter(ExpenseRequest.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    if exp.status != ExpenseStatus.PENDING:
        raise HTTPException(status_code=400, detail="Expense is not pending")

    exp.current_step += 1
    if exp.current_step >= exp.total_steps:
        exp.status = ExpenseStatus.ALL_APPROVED

    db.commit()
    db.refresh(exp)
    return _expense_to_dict(exp)


@router.put("/{expense_id}/reject")
def reject_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exp = db.query(ExpenseRequest).options(
        joinedload(ExpenseRequest.attachments), joinedload(ExpenseRequest.user)
    ).filter(ExpenseRequest.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    if exp.status not in (ExpenseStatus.PENDING, ExpenseStatus.ALL_APPROVED):
        raise HTTPException(status_code=400, detail="Cannot reject this expense")

    exp.status = ExpenseStatus.REJECTED
    exp.rejected_by = current_user.id
    exp.rejected_at = datetime.utcnow()
    db.commit()
    db.refresh(exp)
    return _expense_to_dict(exp)


# ───────── ADMIN: LIST ALL / CONFIRM / EDIT ─────────

@router.get("/all")
def get_all_expenses(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above),
):
    query = (
        db.query(ExpenseRequest)
        .options(joinedload(ExpenseRequest.attachments), joinedload(ExpenseRequest.user))
    )
    if status:
        query = query.filter(ExpenseRequest.status == ExpenseStatus(status))
    return [_expense_to_dict(e) for e in query.order_by(ExpenseRequest.created_at.desc()).all()]


class ExpenseEditBody(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    other_cost: Optional[float] = None


@router.put("/{expense_id}/confirm")
def confirm_expense(
    expense_id: int,
    body: Optional[ExpenseEditBody] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above),
):
    exp = db.query(ExpenseRequest).options(
        joinedload(ExpenseRequest.attachments), joinedload(ExpenseRequest.user)
    ).filter(ExpenseRequest.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    if exp.status != ExpenseStatus.ALL_APPROVED:
        raise HTTPException(status_code=400, detail="Expense must be ALL_APPROVED before confirming")

    # Allow editing before confirm
    if body:
        if body.amount is not None:
            exp.amount = body.amount
        if body.description is not None:
            exp.description = body.description
        if body.other_cost is not None:
            exp.other_cost = body.other_cost
            if exp.expense_type == ExpenseType.TRAVEL:
                exp.total_amount = exp.travel_cost + body.other_cost
                exp.amount = exp.total_amount

    exp.status = ExpenseStatus.CONFIRMED
    exp.confirmed_by = current_user.id
    exp.confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(exp)
    return _expense_to_dict(exp)


@router.put("/{expense_id}/admin-reject")
def admin_reject_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above),
):
    exp = db.query(ExpenseRequest).options(
        joinedload(ExpenseRequest.attachments), joinedload(ExpenseRequest.user)
    ).filter(ExpenseRequest.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    exp.status = ExpenseStatus.REJECTED
    exp.rejected_by = current_user.id
    exp.rejected_at = datetime.utcnow()
    db.commit()
    db.refresh(exp)
    return _expense_to_dict(exp)


# ───────── REPORT ─────────

@router.get("/report")
def get_expense_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_ids: Optional[List[int]] = Query(None),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_gm_or_above),
):
    query = (
        db.query(ExpenseRequest)
        .options(joinedload(ExpenseRequest.attachments), joinedload(ExpenseRequest.user))
    )
    if user_ids:
        query = query.filter(ExpenseRequest.user_id.in_(user_ids))
    if start_date:
        query = query.filter(
            (ExpenseRequest.expense_date >= start_date) | (ExpenseRequest.travel_date >= start_date)
        )
    if end_date:
        query = query.filter(
            (ExpenseRequest.expense_date <= end_date) | (ExpenseRequest.travel_date <= end_date)
        )
    if status:
        query = query.filter(ExpenseRequest.status == ExpenseStatus(status))

    return [_expense_to_dict(e) for e in query.order_by(ExpenseRequest.created_at.desc()).all()]
