from datetime import date, datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.settings import settings
from app.models.deadline import Deadline
from app.models.user import User
from app.models.office_override import OfficeOverride

router = APIRouter(prefix="/system", tags=["System"])


# ======================
# helpers
# ======================
def override_active(db: Session, office_id: int) -> bool:
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


# ======================
# STATUS
# ======================
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

    open_total = q_open.count()
    open_critical = q_open.filter(Deadline.is_critical.is_(True)).count()
    overdue_total = q_open.filter(Deadline.due_date < today).count()

    overdue_critical_items = (
        q_open.filter(
            Deadline.due_date < today,
            Deadline.is_critical.is_(True),
        )
        .order_by(Deadline.due_date.asc(), Deadline.id.asc())
        .limit(10)
        .all()
    )

    override_is_active = override_active(db, user.office_id)
    blocked = (len(overdue_critical_items) > 0) and (not override_is_active)

    next_deadline = (
        q_open.filter(Deadline.due_date >= today)
        .order_by(Deadline.due_date.asc(), Deadline.id.asc())
        .first()
    )

    return {
        "now_utc": datetime.now(timezone.utc).isoformat(),
        "office_id": user.office_id,
        "user_id": user.id,
        "blocked": blocked,
        "override_active": override_is_active,
        "counts": {
            "open_total": open_total,
            "open_critical": open_critical,
            "overdue_total": overdue_total,
            "overdue_critical": len(overdue_critical_items),
        },
        "overdue_critical": [
            {
                "id": d.id,
                "description": d.description,
                "due_date": d.due_date.isoformat(),
                "process_id": d.process_id,
                "is_critical": bool(d.is_critical),
            }
            for d in overdue_critical_items
        ],
        "next_deadline": None
        if not next_deadline
        else {
            "id": next_deadline.id,
            "description": next_deadline.description,
            "due_date": next_deadline.due_date.isoformat(),
            "process_id": next_deadline.process_id,
            "is_critical": bool(next_deadline.is_critical),
        },
    }


# ======================
# UNLOCK (LETRA B)
# ======================
@router.post("/unlock")
def system_unlock(
    data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    LETRA B:
    - Somente owner
    - Senha mestra do sistema (OFFICE_OVERRIDE_SECRET)
    - Override temporário por X minutos
    """

    # 1) só owner
    if not user.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can unlock the office.",
        )

    password = (data.get("password") or "").strip()
    reason = (data.get("reason") or "Manual unlock").strip()

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required.",
        )

    # 2) senha mestra OU senha do próprio usuário
    from app.auth.service import verify_password
    
    secret = settings.OFFICE_OVERRIDE_SECRET.strip()
    is_master_secret = (password == secret)
    is_user_password = verify_password(password, user.password)

    if not (is_master_secret or is_user_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid unlock password.",
        )

    # 3) duração
    try:
        minutes = int(data.get("minutes") or 30)
    except ValueError:
        minutes = 30

    if minutes < 5:
        minutes = 5
    if minutes > 12 * 60:
        minutes = 12 * 60

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=minutes)

    # 4) se já existe override ativo, não cria outro
    if override_active(db, user.office_id):
        return {
            "ok": True,
            "message": "Override already active.",
            "office_id": user.office_id,
        }

    override = OfficeOverride(
        office_id=user.office_id,
        unlocked_by=user.id,
        reason=reason,
        created_at=now,
        expires_at=expires_at,
    )

    db.add(override)
    db.commit()
    db.refresh(override)

    return {
        "ok": True,
        "message": "Office override enabled.",
        "office_id": user.office_id,
        "override_id": override.id,
        "expires_at": override.expires_at.isoformat(),
        "minutes": minutes,
    }


# ======================
# HEALTH
# ======================
@router.get("/health")
def health():
    return {"ok": True}
