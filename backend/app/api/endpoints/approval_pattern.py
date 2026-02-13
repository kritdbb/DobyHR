from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.approval_pattern import ApprovalPattern, ApprovalPatternStep, ApprovalPatternStepApprover
from app.models.user import User
from app.schemas.approval import ApproverResponse
from app.schemas.approval_pattern import (
    ApprovalPatternCreate,
    ApprovalPatternUpdate,
    ApprovalPatternResponse,
    PatternStepResponse,
    ApplyPatternRequest,
)

router = APIRouter(prefix="/api/approval-patterns", tags=["approval-patterns"])


def _build_pattern_response(pattern: ApprovalPattern) -> dict:
    steps_data = []
    for step in sorted(pattern.steps, key=lambda s: s.step_order):
        approvers_data = []
        for sa in step.approvers:
            approver = sa.approver
            approvers_data.append(
                ApproverResponse(
                    id=sa.id,
                    approver_id=sa.approver_id,
                    approver_name=approver.name if approver else None,
                    approver_surname=approver.surname if approver else None,
                )
            )
        steps_data.append(
            PatternStepResponse(
                id=step.id,
                step_order=step.step_order,
                condition_type=step.condition_type,
                approvers=approvers_data,
            )
        )
    return ApprovalPatternResponse(
        id=pattern.id,
        name=pattern.name,
        steps=steps_data,
    )


@router.get("/", response_model=List[ApprovalPatternResponse])
def list_patterns(db: Session = Depends(get_db)):
    patterns = db.query(ApprovalPattern).all()
    return [_build_pattern_response(p) for p in patterns]


@router.get("/{pattern_id}", response_model=ApprovalPatternResponse)
def get_pattern(pattern_id: int, db: Session = Depends(get_db)):
    pattern = db.query(ApprovalPattern).filter(ApprovalPattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return _build_pattern_response(pattern)


@router.post("/", response_model=ApprovalPatternResponse)
def create_pattern(data: ApprovalPatternCreate, db: Session = Depends(get_db)):
    # Validate approver IDs
    all_ids = set()
    for step in data.steps:
        all_ids.update(step.approver_ids)
    existing = {u[0] for u in db.query(User.id).filter(User.id.in_(all_ids)).all()}
    missing = all_ids - existing
    if missing:
        raise HTTPException(status_code=400, detail=f"Approver IDs not found: {missing}")

    pattern = ApprovalPattern(name=data.name)
    db.add(pattern)
    db.flush()

    for step_data in data.steps:
        step = ApprovalPatternStep(
            pattern_id=pattern.id,
            step_order=step_data.step_order,
            condition_type=step_data.condition_type,
        )
        db.add(step)
        db.flush()
        for approver_id in step_data.approver_ids:
            db.add(ApprovalPatternStepApprover(step_id=step.id, approver_id=approver_id))

    db.commit()
    db.refresh(pattern)
    return _build_pattern_response(pattern)


@router.put("/{pattern_id}", response_model=ApprovalPatternResponse)
def update_pattern(pattern_id: int, data: ApprovalPatternUpdate, db: Session = Depends(get_db)):
    pattern = db.query(ApprovalPattern).filter(ApprovalPattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    if data.name is not None:
        pattern.name = data.name

    # Validate approver IDs
    all_ids = set()
    for step in data.steps:
        all_ids.update(step.approver_ids)
    existing = {u[0] for u in db.query(User.id).filter(User.id.in_(all_ids)).all()}
    missing = all_ids - existing
    if missing:
        raise HTTPException(status_code=400, detail=f"Approver IDs not found: {missing}")

    # Delete old steps (cascade deletes approvers)
    for step in pattern.steps:
        db.delete(step)
    db.flush()

    for step_data in data.steps:
        step = ApprovalPatternStep(
            pattern_id=pattern.id,
            step_order=step_data.step_order,
            condition_type=step_data.condition_type,
        )
        db.add(step)
        db.flush()
        for approver_id in step_data.approver_ids:
            db.add(ApprovalPatternStepApprover(step_id=step.id, approver_id=approver_id))

    db.commit()
    db.refresh(pattern)
    return _build_pattern_response(pattern)


@router.delete("/{pattern_id}")
def delete_pattern(pattern_id: int, db: Session = Depends(get_db)):
    pattern = db.query(ApprovalPattern).filter(ApprovalPattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    db.delete(pattern)
    db.commit()
    return {"message": "Pattern deleted successfully"}
