from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.process import Process
from app.models.email_flow import EmailFlow
from app.schemas.email_flow import EmailFlowCreate, EmailFlowUpdate, EmailFlowOut

from app.services.process_event_service import create_process_event

router = APIRouter(prefix="/email-flows", tags=["Email Flows"])


def _now():
    return datetime.now(timezone.utc)


@router.get("/", response_model=list[EmailFlowOut])
def list_flows(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(EmailFlow)
        .filter(EmailFlow.office_id == user.office_id)
        .order_by(EmailFlow.id.desc())
        .all()
    )


@router.get("/process/{process_id}", response_model=EmailFlowOut)
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
    if not flow:
        raise HTTPException(status_code=404, detail="Email flow not found for this process.")
    return flow


@router.post("/", response_model=EmailFlowOut, status_code=201)
def create_or_enable_flow(
    payload: EmailFlowCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # garante que processo pertence ao office
    proc = (
        db.query(Process)
        .filter(Process.id == payload.process_id, Process.office_id == user.office_id)
        .first()
    )
    if not proc:
        raise HTTPException(status_code=404, detail="Process not found.")

    flow = (
        db.query(EmailFlow)
        .filter(EmailFlow.office_id == user.office_id, EmailFlow.process_id == payload.process_id)
        .first()
    )

    now = _now()

    if flow:
        was_active = bool(flow.active)

        # "reativa" / atualiza configs
        flow.active = payload.active
        flow.interval_days = payload.interval_days
        flow.max_attempts = payload.max_attempts
        flow.template = payload.template
        flow.stop_on_any_upload = payload.stop_on_any_upload

        # reset de stop info se reativar
        if payload.active:
            flow.stopped_at = None
            flow.stopped_reason = None

        flow.updated_at = now
        db.add(flow)
        db.commit()
        db.refresh(flow)

        # ✅ TIMELINE EVENT (reativar vs só atualizar)
        try:
            if (not was_active) and flow.active:
                create_process_event(
                    db=db,
                    office_id=user.office_id,
                    process_id=flow.process_id,
                    type="email_flow_started",
                    title="Cobrança automática ativada",
                    description=f"Fluxo reativado. Intervalo: {flow.interval_days} dias | Máx tentativas: {flow.max_attempts}",
                )
            else:
                create_process_event(
                    db=db,
                    office_id=user.office_id,
                    process_id=flow.process_id,
                    type="email_flow_updated",
                    title="Cobrança atualizada",
                    description=f"Config atualizada. Ativo: {flow.active} | Intervalo: {flow.interval_days} | Máx tentativas: {flow.max_attempts}",
                )
        except Exception:
            pass

        return flow

    flow = EmailFlow(
        office_id=user.office_id,
        process_id=payload.process_id,
        active=payload.active,
        interval_days=payload.interval_days,
        max_attempts=payload.max_attempts,
        attempts=0,
        last_sent_at=None,
        template=payload.template,
        stop_on_any_upload=payload.stop_on_any_upload,
        stopped_reason=None,
        stopped_at=None,
        created_at=now,
        updated_at=now,
    )

    db.add(flow)
    db.commit()
    db.refresh(flow)

    # ✅ TIMELINE EVENT: created (+ se ativo, "started")
    try:
        if flow.active:
            create_process_event(
                db=db,
                office_id=user.office_id,
                process_id=flow.process_id,
                type="email_flow_started",
                title="Cobrança ativada",
                description=f"Fluxo criado e ativado. Intervalo: {flow.interval_days} dias | Máx tentativas: {flow.max_attempts}",
            )
        else:
            create_process_event(
                db=db,
                office_id=user.office_id,
                process_id=flow.process_id,
                type="email_flow_created",
                title="Cobrança criada",
                description="Fluxo criado, mas ainda não está ativo.",
            )
    except Exception:
        pass

    return flow


@router.patch("/{flow_id}", response_model=EmailFlowOut)
def update_flow(
    flow_id: int,
    payload: EmailFlowUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    flow = (
        db.query(EmailFlow)
        .filter(EmailFlow.id == flow_id, EmailFlow.office_id == user.office_id)
        .first()
    )
    if not flow:
        raise HTTPException(status_code=404, detail="Email flow not found.")

    was_active = bool(flow.active)
    now = _now()

    if payload.active is not None:
        flow.active = payload.active
        if payload.active:
            flow.stopped_at = None
            flow.stopped_reason = None

    if payload.interval_days is not None:
        flow.interval_days = payload.interval_days

    if payload.max_attempts is not None:
        flow.max_attempts = payload.max_attempts

    if payload.template is not None:
        flow.template = payload.template

    if payload.stop_on_any_upload is not None:
        flow.stop_on_any_upload = payload.stop_on_any_upload

    flow.updated_at = now

    db.add(flow)
    db.commit()
    db.refresh(flow)

    # ✅ TIMELINE EVENT: se ligou/desligou via PATCH, registra isso; senão, updated
    try:
        if (not was_active) and flow.active:
            create_process_event(
                db=db,
                office_id=user.office_id,
                process_id=flow.process_id,
                type="email_flow_started",
                title="Cobrança ativada",
                description=f"Ativada via atualização. Intervalo: {flow.interval_days} dias | Máx tentativas: {flow.max_attempts}",
            )
        elif was_active and (not flow.active):
            create_process_event(
                db=db,
                office_id=user.office_id,
                process_id=flow.process_id,
                type="email_flow_paused",
                title="Cobrança pausada",
                description="Cobrança desativada via atualização de configuração.",
            )
        else:
            create_process_event(
                db=db,
                office_id=user.office_id,
                process_id=flow.process_id,
                type="email_flow_updated",
                title="Cobrança atualizada",
                description=f"Config atualizada. Ativo: {flow.active} | Intervalo: {flow.interval_days} | Máx tentativas: {flow.max_attempts}",
            )
    except Exception:
        pass

    return flow


@router.post("/{flow_id}/pause", response_model=EmailFlowOut)
def pause_flow(
    flow_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    flow = (
        db.query(EmailFlow)
        .filter(EmailFlow.id == flow_id, EmailFlow.office_id == user.office_id)
        .first()
    )
    if not flow:
        raise HTTPException(status_code=404, detail="Email flow not found.")

    flow.active = False
    flow.stopped_reason = "paused_by_user"
    flow.stopped_at = _now()
    flow.updated_at = _now()

    db.add(flow)
    db.commit()
    db.refresh(flow)

    # ✅ TIMELINE EVENT: paused
    try:
        create_process_event(
            db=db,
            office_id=user.office_id,
            process_id=flow.process_id,
            type="email_flow_paused",
            title="Cobrança pausada",
            description="Cobrança automática foi pausada manualmente.",
        )
    except Exception:
        pass

    return flow


@router.post("/{flow_id}/resume", response_model=EmailFlowOut)
def resume_flow(
    flow_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    flow = (
        db.query(EmailFlow)
        .filter(EmailFlow.id == flow_id, EmailFlow.office_id == user.office_id)
        .first()
    )
    if not flow:
        raise HTTPException(status_code=404, detail="Email flow not found.")

    flow.active = True
    flow.stopped_reason = None
    flow.stopped_at = None
    flow.updated_at = _now()

    db.add(flow)
    db.commit()
    db.refresh(flow)

    # ✅ TIMELINE EVENT: resumed
    try:
        create_process_event(
            db=db,
            office_id=user.office_id,
            process_id=flow.process_id,
            type="email_flow_resumed",
            title="Cobrança retomada",
            description="Cobrança automática foi retomada manualmente.",
        )
    except Exception:
        pass

    return flow


@router.post("/{flow_id}/stop", response_model=EmailFlowOut)
def stop_flow(
    flow_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    flow = (
        db.query(EmailFlow)
        .filter(EmailFlow.id == flow_id, EmailFlow.office_id == user.office_id)
        .first()
    )
    if not flow:
        raise HTTPException(status_code=404, detail="Email flow not found.")

    flow.active = False
    flow.stopped_reason = "stopped_by_user"
    flow.stopped_at = _now()
    flow.updated_at = _now()

    db.add(flow)
    db.commit()
    db.refresh(flow)

    # ✅ TIMELINE EVENT: stopped
    try:
        create_process_event(
            db=db,
            office_id=user.office_id,
            process_id=flow.process_id,
            type="email_flow_stopped",
            title="Cobrança encerrada",
            description="Cobrança automática foi encerrada manualmente.",
        )
    except Exception:
        pass

    return flow
