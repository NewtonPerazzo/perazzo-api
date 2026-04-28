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


def send_password_reset_email(to_email: str, token: str) -> None:
    reset_url = build_password_reset_url(token)

    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        logger.warning("SMTP is not configured. Password reset link for %s: %s", to_email, reset_url)
        return

    message = EmailMessage()
    message["Subject"] = "Reset your Perazzo Manager password"
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message.set_content(
        "\n".join(
            [
                "We received a request to reset your Perazzo Manager password.",
                "",
                f"Open this link to create a new password: {reset_url}",
                "",
                "If you did not request this, you can ignore this email."
            ]
        )
    )

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception as exc:
        logger.exception("Failed to send password reset email to %s", to_email)
        raise EmailDeliveryError("Could not send password reset email") from exc
