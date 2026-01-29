from datetime import date, datetime, timezone
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.deadline import Deadline
from app.models.user import User
from app.models.office_override import OfficeOverride


def _override_active(db: Session, office_id: int) -> bool:
    now = datetime.now(timezone.utc)
    return (
        db.query(OfficeOverride.id)
        .filter(
            OfficeOverride.office_id == office_id,
            OfficeOverride.expires_at > now,
        )
        .first()
        is not None
    )


def ensure_office_not_blocked(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    today = date.today()

    # ✅ se existe override ativo, libera
    if _override_active(db, user.office_id):
        return user

    overdue_critical = (
        db.query(Deadline)
        .filter(
            Deadline.office_id == user.office_id,
            Deadline.is_critical.is_(True),
            Deadline.completed.is_(False),
            Deadline.due_date < today,
        )
        .order_by(Deadline.due_date.asc(), Deadline.id.asc())
        .limit(10)
        .all()
    )

    if overdue_critical:
        next_deadline = (
            db.query(Deadline)
            .filter(
                Deadline.office_id == user.office_id,
                Deadline.completed.is_(False),
                Deadline.due_date >= today,
            )
            .order_by(Deadline.due_date.asc(), Deadline.id.asc())
            .first()
        )
        

        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "error": "OFFICE_BLOCKED",
                "message": "Office blocked: there is an overdue critical deadline.",
                "office_id": user.office_id,
                "overdue_critical_count": len(overdue_critical),
                "overdue_critical": [
                    {
                        "id": d.id,
                        "description": d.description,
                        "due_date": d.due_date.isoformat(),
                        "process_id": d.process_id,
                        "is_critical": bool(d.is_critical),
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
                    "process_id": next_deadline.process_id,
                    "is_critical": bool(next_deadline.is_critical),
                    "status": getattr(next_deadline, "status", "pending"),
                },
            },
        )

    return user
