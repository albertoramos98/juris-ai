from datetime import datetime
from sqlalchemy.orm import Session
from app.models.email_flow import EmailFlow


def stop_email_flows_on_document_upload(
    db: Session,
    office_id: int,
    process_id: int,
    reason: str = "Documento enviado (upload)",
) -> int:
    flows = (
        db.query(EmailFlow)
        .filter(
            EmailFlow.office_id == office_id,
            EmailFlow.process_id == process_id,
            EmailFlow.active == True,
            EmailFlow.stop_on_any_upload == True,
        )
        .all()
    )

    if not flows:
        return 0

    now = datetime.utcnow()
    for flow in flows:
        flow.active = False
        flow.stopped_reason = reason
        flow.stopped_at = now

    db.commit()
    return len(flows)
