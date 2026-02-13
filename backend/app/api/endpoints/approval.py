from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.approval import ApprovalFlow, ApprovalStep, ApprovalStepApprover
from app.models.user import User
from app.schemas.approval import (
    ApprovalFlowCreate,
    ApprovalFlowUpdate,
    ApprovalFlowResponse,
    ApprovalStepResponse,
    ApproverResponse,
)

router = APIRouter(prefix="/api/approval-flows", tags=["approval-flows"])


def _build_flow_response(flow: ApprovalFlow) -> dict:
    """Build a response dict from an ApprovalFlow ORM object."""
    steps_data = []
    for step in sorted(flow.steps, key=lambda s: s.step_order):
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
            ApprovalStepResponse(
                id=step.id,
                step_order=step.step_order,
                condition_type=step.condition_type,
                approvers=approvers_data,
            )
        )

    target_user = flow.target_user
    return ApprovalFlowResponse(
        id=flow.id,
        name=flow.name,
        target_user_id=flow.target_user_id,
        target_user_name=f"{target_user.name} {target_user.surname}" if target_user else None,
        steps=steps_data,
    )


@router.get("/", response_model=List[ApprovalFlowResponse])
def list_approval_flows(db: Session = Depends(get_db)):
    flows = db.query(ApprovalFlow).all()
    return [_build_flow_response(f) for f in flows]


@router.get("/user/{user_id}", response_model=ApprovalFlowResponse)
def get_approval_flow_by_user(user_id: int, db: Session = Depends(get_db)):
    flow = db.query(ApprovalFlow).filter(ApprovalFlow.target_user_id == user_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Approval flow not found for this user")
    return _build_flow_response(flow)


@router.get("/{flow_id}", response_model=ApprovalFlowResponse)
def get_approval_flow(flow_id: int, db: Session = Depends(get_db)):
    flow = db.query(ApprovalFlow).filter(ApprovalFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Approval flow not found")
    return _build_flow_response(flow)


@router.post("/", response_model=ApprovalFlowResponse)
def create_approval_flow(data: ApprovalFlowCreate, db: Session = Depends(get_db)):
    # Verify target user exists
    target_user = db.query(User).filter(User.id == data.target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    # Check if flow already exists for this user
    existing = db.query(ApprovalFlow).filter(
        ApprovalFlow.target_user_id == data.target_user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Approval flow already exists for this user. Use PUT to update.",
        )

    # Validate all approver IDs exist
    all_approver_ids = set()
    for step in data.steps:
        all_approver_ids.update(step.approver_ids)

    existing_users = db.query(User.id).filter(User.id.in_(all_approver_ids)).all()
    existing_ids = {u[0] for u in existing_users}
    missing = all_approver_ids - existing_ids
    if missing:
        raise HTTPException(
            status_code=400, detail=f"Approver user IDs not found: {missing}"
        )

    # Create the flow
    flow = ApprovalFlow(
        name=data.name or f"Approval for {target_user.name} {target_user.surname}",
        target_user_id=data.target_user_id,
    )
    db.add(flow)
    db.flush()

    # Create steps and approvers
    for step_data in data.steps:
        step = ApprovalStep(
            flow_id=flow.id,
            step_order=step_data.step_order,
            condition_type=step_data.condition_type,
        )
        db.add(step)
        db.flush()

        for approver_id in step_data.approver_ids:
            approver = ApprovalStepApprover(
                step_id=step.id,
                approver_id=approver_id,
            )
            db.add(approver)

    db.commit()
    db.refresh(flow)
    return _build_flow_response(flow)


@router.put("/{flow_id}", response_model=ApprovalFlowResponse)
def update_approval_flow(
    flow_id: int, data: ApprovalFlowUpdate, db: Session = Depends(get_db)
):
    flow = db.query(ApprovalFlow).filter(ApprovalFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Approval flow not found")

    # Update name if provided
    if data.name is not None:
        flow.name = data.name

    # Validate all approver IDs exist
    all_approver_ids = set()
    for step in data.steps:
        all_approver_ids.update(step.approver_ids)

    existing_users = db.query(User.id).filter(User.id.in_(all_approver_ids)).all()
    existing_ids = {u[0] for u in existing_users}
    missing = all_approver_ids - existing_ids
    if missing:
        raise HTTPException(
            status_code=400, detail=f"Approver user IDs not found: {missing}"
        )

    # Delete old steps (cascade will delete approvers)
    for step in flow.steps:
        db.delete(step)
    db.flush()

    # Create new steps
    for step_data in data.steps:
        step = ApprovalStep(
            flow_id=flow.id,
            step_order=step_data.step_order,
            condition_type=step_data.condition_type,
        )
        db.add(step)
        db.flush()

        for approver_id in step_data.approver_ids:
            approver = ApprovalStepApprover(
                step_id=step.id,
                approver_id=approver_id,
            )
            db.add(approver)

    db.commit()
    db.refresh(flow)
    return _build_flow_response(flow)


@router.delete("/{flow_id}")
def delete_approval_flow(flow_id: int, db: Session = Depends(get_db)):
    flow = db.query(ApprovalFlow).filter(ApprovalFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Approval flow not found")
    db.delete(flow)
    db.commit()
    return {"message": "Approval flow deleted successfully"}


@router.post("/from-pattern", response_model=ApprovalFlowResponse)
def create_flow_from_pattern(
    target_user_id: int,
    pattern_id: int,
    db: Session = Depends(get_db),
):
    from app.models.approval_pattern import ApprovalPattern as PatternModel

    # Verify target user
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    # Check no existing flow
    existing = db.query(ApprovalFlow).filter(ApprovalFlow.target_user_id == target_user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Approval flow already exists for this user. Delete it first or use PUT to update.")

    # Get pattern
    pattern = db.query(PatternModel).filter(PatternModel.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    # Create flow from pattern
    flow = ApprovalFlow(
        name=f"Approval for {target_user.name} {target_user.surname}",
        target_user_id=target_user_id,
    )
    db.add(flow)
    db.flush()

    for pattern_step in sorted(pattern.steps, key=lambda s: s.step_order):
        step = ApprovalStep(
            flow_id=flow.id,
            step_order=pattern_step.step_order,
            condition_type=pattern_step.condition_type,
        )
        db.add(step)
        db.flush()
        for pa in pattern_step.approvers:
            db.add(ApprovalStepApprover(step_id=step.id, approver_id=pa.approver_id))

    db.commit()
    db.refresh(flow)
    return _build_flow_response(flow)
