from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.email_flow import EmailFlow
from app.models.process import Process
from app.models.client import Client
from app.models.document import Document

from app.models.process_event import ProcessEvent
from app.services.email_service import send_email_smtp
from app.services.process_event_service import create_process_event


_scheduler: BackgroundScheduler | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _has_any_uploaded_doc(db: Session, office_id: int, process_id: int) -> bool:
    q = (
        db.query(Document.id)
        .filter(Document.office_id == office_id, Document.process_id == process_id)
        .limit(1)
    )
    return db.query(q.exists()).scalar()  # type: ignore


def _stop_flow(db: Session, flow: EmailFlow, reason: str):
    flow.active = False
    flow.stopped_reason = reason
    flow.stopped_at = _now()
    flow.updated_at = _now()
    db.add(flow)


def _is_due(flow: EmailFlow) -> bool:
    if not flow.last_sent_at:
        return True

    interval = timedelta(days=int(flow.interval_days or 3))
    return (_now() - flow.last_sent_at) >= interval


def _render_email(template: str, proc: Process, client: Client | None) -> tuple[str, str]:
    client_name = (client.name if client else "Cliente").strip()
    proc_number = (getattr(proc, "number", None) or "").strip()
    court = (getattr(proc, "court", None) or "").strip()
    kind = (getattr(proc, "type", None) or "").strip()

    if template == "cobranca_docs":
        subject = f"[Juris AI] Documentos pendentes — Processo {proc_number or proc.id}"
        body = (
            f"Olá, {client_name}!\n\n"
            f"Estamos precisando dos documentos para dar andamento no processo.\n\n"
            f"Processo: {proc_number or f'#{proc.id}'}\n"
            f"Vara: {court or '-'}\n"
            f"Tipo: {kind or '-'}\n\n"
            f"Se você já enviou, pode desconsiderar este e-mail.\n\n"
            f"Atenciosamente,\n"
            f"Juris AI\n"
        )
        return subject, body

    subject = f"[Juris AI] Atualização — Processo {proc_number or proc.id}"
    body = (
        f"Olá, {client_name}!\n\n"
        f"Mensagem automática do Juris AI referente ao processo {proc_number or f'#{proc.id}'}.\n\n"
        f"Atenciosamente,\nJuris AI\n"
    )
    return subject, body


def tick_email_flows():
    """
    Rodada única (chamada pelo APScheduler).
    - busca flows ativos
    - verifica regras (max_attempts, stop_on_upload, due)
    - envia e-mail e atualiza contadores
    """
    db = SessionLocal()
    try:
        flows: list[EmailFlow] = (
            db.query(EmailFlow)
            .filter(EmailFlow.active == True)  # noqa: E712
            .order_by(EmailFlow.id.asc())
            .all()
        )

        for flow in flows:
            # regra 1: se chegou no max_attempts, encerra
            if int(flow.attempts or 0) >= int(flow.max_attempts or 10):
                _stop_flow(db, flow, "max_attempts_reached")
                try:
                    create_process_event(
                        db=db,
                        office_id=flow.office_id,
                        process_id=flow.process_id,
                        type="email_flow_stopped",
                        title="Cobrança encerrada automaticamente",
                        description="Encerrado por atingir o número máximo de tentativas.",
                    )
                except Exception:
                    pass
                db.commit()
                continue

            # regra 2: se configurado, para quando existir qualquer upload
            if bool(flow.stop_on_any_upload):
                if _has_any_uploaded_doc(db, flow.office_id, flow.process_id):
                    _stop_flow(db, flow, "doc_uploaded")
                    try:
                        create_process_event(
                            db=db,
                            office_id=flow.office_id,
                            process_id=flow.process_id,
                            type="email_flow_stopped",
                            title="Cobrança encerrada automaticamente",
                            description="Encerrado porque foi detectado upload de documento no processo.",
                        )
                    except Exception:
                        pass
                    db.commit()
                    continue

            # regra 3: só envia se estiver na hora
            if not _is_due(flow):
                continue

            # pega processo + cliente
            proc = (
                db.query(Process)
                .filter(Process.id == flow.process_id, Process.office_id == flow.office_id)
                .first()
            )
            if not proc:
                _stop_flow(db, flow, "process_not_found")
                try:
                    create_process_event(
                        db=db,
                        office_id=flow.office_id,
                        process_id=flow.process_id,
                        type="email_flow_stopped",
                        title="Cobrança encerrada automaticamente",
                        description="Encerrado porque o processo não foi encontrado.",
                    )
                except Exception:
                    pass
                db.commit()
                continue

            client = (
                db.query(Client)
                .filter(Client.id == proc.client_id, Client.office_id == flow.office_id)
                .first()
            )

            to_email = getattr(client, "email", None) if client else None
            if not to_email:
                _stop_flow(db, flow, "no_client_email")
                try:
                    create_process_event(
                        db=db,
                        office_id=flow.office_id,
                        process_id=flow.process_id,
                        type="email_flow_stopped",
                        title="Cobrança encerrada automaticamente",
                        description="Encerrado porque o cliente não possui e-mail cadastrado.",
                    )
                except Exception:
                    pass
                db.commit()
                continue

            subject, body = _render_email(flow.template, proc, client)

            # tenta enviar; mesmo se falhar, conta tentativa pra não loopar infinito
            try:
                send_email_smtp(to_email=str(to_email), subject=subject, body=body)
                
                flow.attempts = int(flow.attempts or 0) + 1
                flow.last_sent_at = _now()
                flow.updated_at = _now()

                # ✅ TIMELINE EVENT: email_sent
                try:
                    create_process_event(
                        db=db,
                        office_id=flow.office_id,
                        process_id=flow.process_id,
                        type="email_sent",
                        title="E-mail enviado",
                        description=f"E-mail automático enviado para {to_email} (tentativa {flow.attempts}/{flow.max_attempts or 10}).",
                    )
                except Exception:
                    pass

            except Exception as e:
                flow.attempts = int(flow.attempts or 0) + 1
                flow.last_sent_at = _now()
                flow.updated_at = _now()
                
                # ✅ TIMELINE EVENT: email_send_failed
                try:
                    create_process_event(
                        db=db,
                        office_id=flow.office_id,
                        process_id=flow.process_id,
                        type="email_send_failed",
                        title="Falha ao enviar e-mail",
                        description=f"Tentativa {flow.attempts}/{flow.max_attempts or 10}. Erro: {str(e)[:180]}",
                    )
                except Exception:
                    pass

                print(f"[EMAIL_SCHEDULER] send failed flow={flow.id}: {e}")

            # se bateu max_attempts após tentativa (sucesso ou falha), já encerra
            if int(flow.attempts) >= int(flow.max_attempts or 10):
                flow.active = False
                flow.stopped_reason = "max_attempts_reached"
                flow.stopped_at = _now()

                try:
                    create_process_event(
                        db=db,
                        office_id=flow.office_id,
                        process_id=flow.process_id,
                        type="email_flow_stopped",
                        title="Cobrança encerrada automaticamente",
                        description="Encerrado por atingir o número máximo de tentativas.",
                    )
                except Exception:
                    pass

            db.add(flow)
            db.commit()

            print(
                f"[EMAIL_SCHEDULER] sent flow={flow.id} "
                f"attempts={flow.attempts}/{flow.max_attempts} "
                f"process={flow.process_id} to={to_email}"
            )

    finally:
        db.close()


def start_email_scheduler():
    """
    Chame isso no startup do FastAPI.
    """
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        tick_email_flows,
        trigger=IntervalTrigger(seconds=60),
        id="email_flow_tick",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    print("[EMAIL_SCHEDULER] APScheduler started ✅")


def stop_email_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        print("[EMAIL_SCHEDULER] APScheduler stopped ✅")
