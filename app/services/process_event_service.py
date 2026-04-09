from sqlalchemy.orm import Session
from app.models.process_event import ProcessEvent


def create_process_event(
    db: Session,
    *,
    office_id: int,
    process_id: int,
    type: str,
    title: str,
    description: str | None = None,
):
    """
    Cria um evento de timeline do processo.

    - type: string curta (ex: "deadline_created", "document_uploaded")
    - title: frase curta pra UI
    - description: texto mais humano/detalhado (opcional)
    """
    event = ProcessEvent(
        office_id=office_id,
        process_id=process_id,
        type=type,
        title=title,
        description=description,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
