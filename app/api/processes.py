from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.permissions.dependencies import ensure_office_not_blocked

from app.models.process import Process
from app.models.client import Client
from app.models.user import User
from app.schemas.process import ProcessCreate, ProcessResponse

router = APIRouter(prefix="/processes", tags=["processes"])


@router.post("/", response_model=ProcessResponse)
def create_process(
    data: ProcessCreate,
    db: Session = Depends(get_db),
    user: User = Depends(ensure_office_not_blocked),
):
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
    )

    db.add(process)
    db.commit()
    db.refresh(process)
    return process


@router.get("/", response_model=list[ProcessResponse])
def list_processes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Process)
        .filter(Process.office_id == user.office_id)
        .all()
    )
