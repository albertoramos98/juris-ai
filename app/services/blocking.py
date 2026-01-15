from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.deadline import Deadline
from app.models.user_block import UserBlock

def recalc_user_block(db: Session, office_id: int, user_id: int):
    now = datetime.now(timezone.utc)

    overdue_critical = (
        db.query(Deadline)
        .filter(
            Deadline.office_id == office_id,
            Deadline.assigned_to_id == user_id,  # se você tiver esse campo; se não tiver, tira essa linha
            Deadline.is_critical.is_(True),
            Deadline.status != "done",
            Deadline.due_date < now,
        )
        .first()
    )

    existing = (
        db.query(UserBlock)
        .filter(
            UserBlock.office_id == office_id,
            UserBlock.user_id == user_id,
            UserBlock.resolved_at.is_(None),
        )
        .first()
    )

    if overdue_critical and not existing:
        db.add(UserBlock(office_id=office_id, user_id=user_id))
        db.commit()
        return "blocked"

    if not overdue_critical and existing:
        existing.resolved_at = now
        db.commit()
        return "unblocked"

    return "no_change"
