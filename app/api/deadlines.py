from datetime import date, datetime, time, timedelta, timezone

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.deadline import Deadline
from app.models.user import User
from app.permissions.dependencies import ensure_office_not_blocked
from app.services.google_oauth import get_valid_access_token

router = APIRouter(prefix="/deadlines", tags=["Deadlines"])


@router.get("/")
def list_deadlines(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Deadline)
        .filter(Deadline.office_id == user.office_id)
        .order_by(Deadline.due_date.asc(), Deadline.id.asc())
        .all()
    )


@router.post("/", dependencies=[Depends(ensure_office_not_blocked)])
def create_deadline(
    data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    description = (data.get("description") or "").strip()
    due_date = data.get("due_date")
    responsible = (data.get("responsible") or "").strip()
    process_id = data.get("process_id")
    is_critical = bool(data.get("is_critical"))

    if not description or not due_date or not responsible or not process_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields.",
        )

    deadline = Deadline(
        description=description,
        due_date=due_date,
        responsible=responsible,
        process_id=process_id,
        is_critical=is_critical,
        office_id=user.office_id,
        completed=False,
        status="pending",
    )

    db.add(deadline)
    db.commit()
    db.refresh(deadline)

    return deadline


@router.post("/{deadline_id}/complete")
def complete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = (
        db.query(Deadline)
        .filter(Deadline.id == deadline_id, Deadline.office_id == user.office_id)
        .first()
    )
    if not d:
        raise HTTPException(status_code=404, detail="Deadline not found.")

    if d.completed:
        return {"ok": True, "message": "Deadline already completed."}

    # regra: prazo crítico vencido só owner pode concluir
    if d.is_critical and d.due_date < date.today() and not user.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can complete overdue critical deadline.",
        )

    d.completed = True
    d.status = "done"
    d.completed_at = datetime.now(timezone.utc)
    d.completed_by = user.id

    db.add(d)
    db.commit()

    return {"ok": True, "deadline_id": d.id}


@router.post("/{deadline_id}/sync_calendar")
def sync_deadline_to_calendar(
    deadline_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = (
        db.query(Deadline)
        .filter(Deadline.id == deadline_id, Deadline.office_id == user.office_id)
        .first()
    )
    if not d:
        raise HTTPException(status_code=404, detail="Deadline not found.")

    token = get_valid_access_token(db, user.office_id)

    start_dt = datetime.combine(d.due_date, time(10, 0)).replace(tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(minutes=30)

    payload = {
        "summary": f"Prazo #{d.id} — {d.description}",
        "description": (
            f"Prazo criado no Juris AI\n\n"
            f"ID: {d.id}\n"
            f"Responsável: {d.responsible}\n"
            f"Crítico: {'SIM' if d.is_critical else 'não'}\n"
            f"Processo ID: {d.process_id}"
        ),
        "start": {"dateTime": start_dt.isoformat()},
        "end": {"dateTime": end_dt.isoformat()},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }

    r = requests.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )

    if r.status_code not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calendar create failed ({r.status_code}): {r.text}",
        )

    ev = r.json()

    organizer_email = (
        (ev.get("organizer") or {}).get("email")
        or (ev.get("creator") or {}).get("email")
        or ""
    )

    html_link = ev.get("htmlLink")
    open_link = html_link
    if html_link and organizer_email:
        sep = "&" if "?" in html_link else "?"
        open_link = f"{html_link}{sep}authuser={organizer_email}"

    return {
        "ok": True,
        "deadline_id": d.id,
        "calendar_event_id": ev.get("id"),
        "htmlLink": html_link,
        "openLink": open_link,  # ✅ abre esse no front
        "organizer_email": organizer_email,
        "start": ev.get("start"),
        "end": ev.get("end"),
        "created": ev.get("created"),
    }
