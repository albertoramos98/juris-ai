import requests
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.google_oauth import get_valid_access_token

router = APIRouter(prefix="/google/calendar", tags=["Google - Calendar"])


@router.get("/upcoming")
def calendar_upcoming(
    max_results: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    token = get_valid_access_token(db, user.office_id)

    now = datetime.now(timezone.utc).isoformat()
    params = {
        "timeMin": now,
        "maxResults": max(1, min(max_results, 50)),
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    r = requests.get(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


@router.post("/events")
def calendar_create_event(
    data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    data:
      - summary: str
      - description: str (opcional)
      - start: ISO datetime (ex: 2026-01-20T14:00:00-03:00)
      - end:   ISO datetime (ex: 2026-01-20T15:00:00-03:00)
    """
    token = get_valid_access_token(db, user.office_id)

    summary = (data.get("summary") or "").strip()
    start = (data.get("start") or "").strip()
    end = (data.get("end") or "").strip()
    description = (data.get("description") or "").strip()

    if not summary or not start or not end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="summary, start and end are required.",
        )

    payload = {
        "summary": summary,
        "description": description or None,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
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
    r.raise_for_status()
    return r.json()
