import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    pass


def build_password_reset_url(token: str) -> str:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    return f"{frontend_url}/reset-password?token={quote(token)}"


def build_email_verification_url(token: str) -> str:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    return f"{frontend_url}/verify-email?token={quote(token)}"


def _send_email(to_email: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL or (settings.SMTP_USER and not settings.SMTP_PASSWORD):
        logger.warning("SMTP is not configured. Email to %s was not sent.", to_email)
        raise EmailDeliveryError("Email service is not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception as exc:
        logger.exception("Failed to send email to %s", to_email)
        raise EmailDeliveryError("Could not send email") from exc


def send_password_reset_email(to_email: str, token: str) -> None:
    reset_url = build_password_reset_url(token)
    _send_email(
        to_email,
        "Reset your Perazzo Manager password",
        "\n".join(
            [
                "We received a request to reset your Perazzo Manager password.",
                "",
                f"Open this link to create a new password: {reset_url}",
                "",
                "If you did not request this, you can ignore this email."
            ]
        ),
    )


def send_email_verification_email(to_email: str, token: str) -> None:
    verification_url = build_email_verification_url(token)
    _send_email(
        to_email,
        "Verify your Perazzo Manager email",
        "\n".join(
            [
                "Welcome to Perazzo Manager.",
                "",
                f"Open this link to verify your email: {verification_url}",
                "",
                "If you did not create this account, you can ignore this email."
            ]
        ),
    )
