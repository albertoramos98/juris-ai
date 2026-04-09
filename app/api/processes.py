from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.permissions.dependencies import ensure_office_not_blocked

from app.models.process_event import ProcessEvent
from app.models.process import Process
from app.models.client import Client
from app.models.user import User
from app.schemas.process import ProcessCreate, ProcessResponse

from app.services.process_event_service import create_process_event

router = APIRouter(prefix="/processes", tags=["processes"])


@router.post("/", response_model=ProcessResponse)
def create_process(
    data: ProcessCreate,
    db: Session = Depends(get_db),
    user: User = Depends(ensure_office_not_blocked),
):
    # 1) verifica se o número do processo já existe para aquele escritório
    existing_process = (
        db.query(Process)
        .filter(
            Process.number == data.number,
            Process.office_id == user.office_id,
        )
        .first()
    )

    if existing_process:
        raise HTTPException(
            status_code=400,
            detail=f"Processo com o número {data.number} já cadastrado para este escritório",
        )

    # 2) verifica se o cliente pertence ao escritório
    client = (
        db.query(Client)
        .filter(
            Client.id == data.client_id,
            Client.office_id == user.office_id,
        )
        .first()
    )

    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    process = Process(
        number=data.number,
        court=data.court,
        type=data.type,
        client_id=data.client_id,
        office_id=user.office_id,
        status=data.status or "ativo",
    )

    db.add(process)
    db.commit()
    db.refresh(process)

    # Re-load with relationship for the response_model
    process = (
        db.query(Process)
        .options(joinedload(Process.client))
        .filter(Process.id == process.id)
        .first()
    )

    # ✅ EVENTO: process created
    try:
        create_process_event(
            db=db,
            office_id=user.office_id,
            process_id=process.id,
            type="process_created",
            description=f"Processo criado: {process.number or process.id}",
            meta={"client_id": process.client_id, "court": process.court, "type": process.type},
            actor_user_id=user.id,
        )
    except Exception:
        # não quebra a criação do processo se event falhar
        pass

    return process


@router.get("/{process_id}/events")
def list_process_events(
    process_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # garante que o processo existe e pertence ao office
    proc = (
        db.query(Process)
        .filter(Process.id == process_id, Process.office_id == user.office_id)
        .first()
    )
    if not proc:
        raise HTTPException(status_code=404, detail="Processo não encontrado")

    events = (
        db.query(ProcessEvent)
        .filter(
            ProcessEvent.office_id == user.office_id,
            ProcessEvent.process_id == process_id,
        )
        .order_by(ProcessEvent.created_at.desc())
        .all()
    )
    return events


@router.get("/", response_model=list[ProcessResponse])
def list_processes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Process)
        .options(joinedload(Process.client))
        .filter(Process.office_id == user.office_id)
        .all()
    )
