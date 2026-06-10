import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


def send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        return False


def send_confirmation_email(to_email: str, token: str) -> bool:
    link = f"{settings.FRONTEND_URL}/confirm-email?token={token}"
    body = f"<p>Confirme seu e-mail clicando <a href='{link}'>aqui</a>.</p>"
    return send_email(to_email, "RoutineX - Confirmação de E-mail", body)


def send_reset_password_email(to_email: str, token: str) -> bool:
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    body = f"<p>Redefina sua senha clicando <a href='{link}'>aqui</a>. O link expira em 30 minutos.</p>"
    return send_email(to_email, "RoutineX - Redefinição de Senha", body)
