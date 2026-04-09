import smtplib
from email.message import EmailMessage
from app.core.settings import settings

def send_email_smtp(to_email: str, subject: str, body: str) -> None:
    if not settings.smtp_host or not settings.smtp_from:
        print("[SMTP] Falha: Host ou Remetente não configurados no .env")
        raise RuntimeError("smtp_host e smtp_from precisam estar definidos no .env")

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()

        if settings.smtp_user and settings.smtp_pass:
            server.login(settings.smtp_user, settings.smtp_pass)

        server.send_message(msg)
