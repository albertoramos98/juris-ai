from datetime import date
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.deadline import Deadline
from app.models.user import User


def ensure_office_not_blocked(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    today = date.today()

    # Conta críticos vencidos
    overdue_critical_count = (
        db.query(Deadline.id)
        .filter(
            Deadline.office_id == user.office_id,
            Deadline.is_critical.is_(True),
            Deadline.completed.is_(False),
            Deadline.due_date < today,
        )
        .count()
    )

    if overdue_critical_count > 0:
        # Próximo prazo (aberto) pra UI
        next_deadline = (
            db.query(Deadline)
            .filter(
                Deadline.office_id == user.office_id,
                Deadline.completed.is_(False),
            )
            .order_by(Deadline.due_date.asc(), Deadline.id.asc())
            .first()
        )

        # Lista curta dos críticos vencidos (top 5) pra UI
        overdue_critical = (
            db.query(Deadline)
            .filter(
                Deadline.office_id == user.office_id,
                Deadline.is_critical.is_(True),
                Deadline.completed.is_(False),
                Deadline.due_date < today,
            )
            .order_by(Deadline.due_date.asc(), Deadline.id.asc())
            .limit(5)
            .all()
        )

        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "error": "OFFICE_BLOCKED",
                "message": "Office blocked: there is an overdue critical deadline.",
                "office_id": user.office_id,
                "overdue_critical_count": overdue_critical_count,
                "overdue_critical": [
                    {
                        "id": d.id,
                        "description": d.description,
                        "due_date": d.due_date.isoformat(),
                        "process_id": d.process_id,
                        "status": getattr(d, "status", "pending"),
                    }
                    for d in overdue_critical
                ],
                "next_deadline": None
                if not next_deadline
                else {
                    "id": next_deadline.id,
                    "description": next_deadline.description,
                    "due_date": next_deadline.due_date.isoformat(),
                    "is_critical": bool(next_deadline.is_critical),
                    "process_id": next_deadline.process_id,
                    "status": getattr(next_deadline, "status", "pending"),
                },
            },
        )

    return user
