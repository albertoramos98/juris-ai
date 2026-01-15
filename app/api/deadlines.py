from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.permissions.dependencies import ensure_office_not_blocked

from app.models.deadline import Deadline
from app.models.process import Process
from app.models.user import User
from app.schemas.deadline import DeadlineCreate, DeadlineResponse

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


@router.post("/", response_model=DeadlineResponse)
def create_deadline(
    data: DeadlineCreate,
    db: Session = Depends(get_db),
    user: User = Depends(ensure_office_not_blocked),
):
    process = (
        db.query(Process)
        .filter(
            Process.id == data.process_id,
            Process.office_id == user.office_id,
        )
        .first()
    )

    if not process:
        raise HTTPException(status_code=404, detail="Processo não encontrado")

    deadline = Deadline(
        description=data.description,
        due_date=data.due_date,
        responsible=data.responsible,
        process_id=data.process_id,
        office_id=user.office_id,
        is_critical=data.is_critical,
        status="pending",
        completed=False,
    )

    db.add(deadline)
    db.commit()
    db.refresh(deadline)
    return deadline


@router.get("/", response_model=list[DeadlineResponse])
def list_deadlines(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Deadline)
        .filter(Deadline.office_id == user.office_id)
        .all()
    )


@router.post("/{deadline_id}/complete", response_model=DeadlineResponse)
def complete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deadline = (
        db.query(Deadline)
        .filter(
            Deadline.id == deadline_id,
            Deadline.office_id == user.office_id,
        )
        .first()
    )

    if not deadline:
        raise HTTPException(status_code=404, detail="Prazo não encontrado")

    if deadline.completed:
        return deadline  # idempotente

    today = date.today()
    is_overdue = deadline.due_date < today

    # Regra de governança: crítico + vencido => só owner conclui
    if deadline.is_critical and is_overdue and not user.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o dono do escritório pode concluir prazo crítico vencido.",
        )

    deadline.completed = True
    deadline.completed_at = datetime.utcnow()
    deadline.completed_by = user.id
    deadline.status = "done"

    db.commit()
    db.refresh(deadline)
    return deadline
