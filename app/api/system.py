from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.deadline import Deadline
from app.models.user import User

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/status")
def system_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    today = date.today()

    q_open = (
        db.query(Deadline)
        .filter(
            Deadline.office_id == user.office_id,
            Deadline.completed.is_(False),
        )
    )

    overdue_total = q_open.filter(Deadline.due_date < today).count()

    overdue_critical_count = (
        q_open.filter(
            Deadline.due_date < today,
            Deadline.is_critical.is_(True),
        ).count()
    )

    open_total = q_open.count()

    open_critical = q_open.filter(Deadline.is_critical.is_(True)).count()

    next_deadline = (
        q_open.filter(Deadline.due_date >= today)
        .order_by(Deadline.due_date.asc(), Deadline.id.asc())
        .first()
    )

    overdue_critical = (
        q_open.filter(
            Deadline.due_date < today,
            Deadline.is_critical.is_(True),
        )
        .order_by(Deadline.due_date.asc(), Deadline.id.asc())
        .limit(5)
        .all()
    )

    blocked = overdue_critical_count > 0

    payload = {
        "now_utc": datetime.now(timezone.utc).isoformat(),
        "office_id": user.office_id,
        "user_id": user.id,
        "blocked": blocked,
        "counts": {
            "overdue_total": overdue_total,
            "overdue_critical": overdue_critical_count,
            "open_total": open_total,
            "open_critical": open_critical,
        },
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
    }

    return payload


@router.get("/health")
def health():
    return {"ok": True}
