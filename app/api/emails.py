from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.permissions.dependencies import ensure_office_not_blocked

from app.models.user import User
from app.models.process import Process
from app.models.client import Client
from app.models.email_log import EmailLog

from app.schemas.email import SendEmailRequest, EmailLogResponse
from app.services.email_service import send_email_smtp

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/send", response_model=EmailLogResponse)
def send_email(
    data: SendEmailRequest,
    db: Session = Depends(get_db),
    user: User = Depends(ensure_office_not_blocked),
):
    # processo do mesmo office
    proc = (
        db.query(Process)
        .filter(Process.id == data.process_id, Process.office_id == user.office_id)
        .first()
    )
    if not proc:
        raise HTTPException(status_code=404, detail="Processo não encontrado")

    # cliente do mesmo office
    client = (
        db.query(Client)
        .filter(Client.id == proc.client_id, Client.office_id == user.office_id)
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    if not client.email:
        raise HTTPException(status_code=400, detail="Cliente não possui e-mail cadastrado")

    log = EmailLog(
        office_id=user.office_id,
        process_id=proc.id,
        client_id=client.id,
        to_email=client.email,
        subject=data.subject,
        body=data.body,
        status="sent",
        error=None,
    )

    try:
        send_email_smtp(client.email, data.subject, data.body)
    except Exception as e:
        log.status = "failed"
        log.error = str(e)

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/logs", response_model=list[EmailLogResponse])
def list_logs(
    process_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(EmailLog)
        .filter(EmailLog.office_id == user.office_id, EmailLog.process_id == process_id)
        .order_by(EmailLog.created_at.desc())
        .all()
    )
