from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal

from app.models.email_flow import EmailFlow
from app.models.process import Process
from app.models.client import Client

from app.services.email_service import send_email_smtp


def render_template(template: str, process_number: str) -> tuple[str, str]:
    # templates MVP (simples e vendável)
    if template == "cobranca_docs":
        subject = f"Solicitação de documentos — Processo {process_number}"
        body = (
            f"Olá! Tudo bem?\n\n"
            f"Estamos dando andamento ao processo {process_number}.\n"
            f"Para prosseguirmos, precisamos que você envie os documentos abaixo:\n\n"
            f"- Documento de identificação (RG/CPF)\n"
            f"- Comprovante de residência\n"
            f"- Documentos relacionados ao caso (contratos, prints, comprovantes etc.)\n\n"
            f"Assim que recebermos, confirmamos por aqui.\n\n"
            f"Atenciosamente,\n"
            f"Equipe Juris AI\n"
        )
        return subject, body

    # fallback genérico
    return (
        f"Atualização — Processo {process_number}",
        "Mensagem automática.",
    )


def should_send(flow: EmailFlow) -> bool:
    if not flow.active:
        return False
    if flow.attempts >= flow.max_attempts:
        return False
    if flow.last_sent_at is None:
        return True
    next_time = flow.last_sent_at + timedelta(days=int(flow.interval_days))
    return datetime.utcnow() >= next_time


def run_once() -> None:
    db: Session = SessionLocal()
    try:
        flows = db.query(EmailFlow).filter(EmailFlow.active == True).all()

        sent = 0
        skipped = 0
        stopped = 0

        for flow in flows:
            if not should_send(flow):
                skipped += 1
                continue

            proc = (
                db.query(Process)
                .filter(
                    Process.id == flow.process_id,
                    Process.office_id == flow.office_id,
                )
                .first()
            )
            if not proc:
                flow.active = False
                flow.stopped_reason = "Processo inexistente"
                flow.stopped_at = datetime.utcnow()
                db.commit()
                stopped += 1
                continue

            client = (
                db.query(Client)
                .filter(
                    Client.id == proc.client_id,
                    Client.office_id == flow.office_id,
                )
                .first()
            )
            if not client or not getattr(client, "email", None):
                flow.active = False
                flow.stopped_reason = "Cliente sem e-mail"
                flow.stopped_at = datetime.utcnow()
                db.commit()
                stopped += 1
                continue

            subject, body = render_template(flow.template, proc.number)

            try:
                send_email_smtp(client.email, subject, body)
                flow.last_sent_at = datetime.utcnow()
                flow.attempts = int(flow.attempts or 0) + 1

                # auto-stop ao atingir limite (opcional, mas bom)
                if flow.attempts >= flow.max_attempts:
                    flow.active = False
                    flow.stopped_reason = "Max attempts atingido"
                    flow.stopped_at = datetime.utcnow()

                db.commit()
                sent += 1
                print(f"[EMAIL_FLOW] sent -> process={proc.id} to={client.email} attempts={flow.attempts}/{flow.max_attempts}")

            except Exception as e:
                # Se falhar, NÃO desliga automaticamente: tenta de novo no próximo ciclo.
                # Mas marca last_sent_at pra respeitar o intervalo e não spammar.
                flow.last_sent_at = datetime.utcnow()
                db.commit()
                print(f"[EMAIL_FLOW] failed -> process={proc.id} to={client.email} err={e}")

        print(f"[EMAIL_FLOW] done. sent={sent} skipped={skipped} stopped={stopped}")

    finally:
        db.close()


if __name__ == "__main__":
    run_once()
