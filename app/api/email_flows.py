from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.models.user import User
from app.models.process import Process
from app.models.email_flow import EmailFlow

from app.schemas.email_flow import EmailFlowStart, EmailFlowResponse

router = APIRouter(prefix="/email_flows", tags=["email_flows"])


@router.get("/process/{process_id}", response_model=EmailFlowResponse | None)
def get_flow_by_process(
    process_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    flow = (
        db.query(EmailFlow)
        .filter(
            EmailFlow.office_id == user.office_id,
            EmailFlow.process_id == process_id,
        )
        .first()
    )
    return flow


@router.post("/start", response_model=EmailFlowResponse)
def start_flow(
    payload: EmailFlowStart,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # garante que o processo existe e é do office
    proc = (
        db.query(Process)
        .filter(Process.id == payload.process_id, Process.office_id == user.office_id)
        .first()
    )
    if not proc:
        raise HTTPException(status_code=404, detail="Processo não encontrado")

    flow = (
        db.query(EmailFlow)
        .filter(
            EmailFlow.office_id == user.office_id,
            EmailFlow.process_id == payload.process_id,
        )
        .first()
    )

    if not flow:
        flow = EmailFlow(
            office_id=user.office_id,
            process_id=payload.process_id,
        )
        db.add(flow)

    # ativa/atualiza config
    flow.active = True
    flow.interval_days = int(payload.interval_days)
    flow.max_attempts = int(payload.max_attempts)
    flow.template = payload.template or "cobranca_docs"
    flow.stop_on_any_upload = bool(payload.stop_on_any_upload)

    # reset do stop (se estava parado)
    flow.stopped_reason = None
    flow.stopped_at = None

    db.commit()
    db.refresh(flow)
    return flow


@router.post("/stop/{process_id}", response_model=EmailFlowResponse)
def stop_flow(
    process_id: int,
    reason: str = "Manual stop",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    flow = (
        db.query(EmailFlow)
        .filter(
            EmailFlow.office_id == user.office_id,
            EmailFlow.process_id == process_id,
        )
        .first()
    )
    if not flow:
        raise HTTPException(status_code=404, detail="Flow não encontrado")

    flow.active = False
    flow.stopped_reason = reason or "Manual stop"
    flow.stopped_at = datetime.utcnow()

    db.commit()
    db.refresh(flow)
    return flow
