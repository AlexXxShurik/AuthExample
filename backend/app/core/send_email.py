import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from email_validator import validate_email, EmailNotValidError
from fastapi import BackgroundTasks, Request
from pydantic import EmailStr, ValidationError

from backend.app.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: EmailStr,
    subject: str,
    body: str,
    file_content: bytes = None,
    filename: str = None,
) -> None:
    """
    Отправляет email через SMTP
    """
    try:
        valid = validate_email(str(to_email))
        to_email = valid.normalized

        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_USERNAME
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        if file_content and filename:
            part = MIMEApplication(file_content, Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)

        with smtplib.SMTP_SSL(
            host=settings.SMTP_SERVER, port=settings.SMTP_PORT
        ) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Письмо успешно отправлено на {to_email}")

    except (EmailNotValidError, ValidationError) as e:
        logger.error(f"Ошибка валидации email: {e}")
    except smtplib.SMTPAuthenticationError:
        logger.error("Ошибка аутентификации: проверьте логин и пароль SMTP")
    except smtplib.SMTPException as e:
        logger.error(f"Ошибка SMTP: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отправке письма: {e}")


def send_verification_email(
    background_tasks: BackgroundTasks, request: Request, email: EmailStr, token: str
):

    server_url = str(request.base_url).rstrip("/")
    verification_url = f"{server_url}/v1/auth/verify-email?token={token}"

    message = f"""
    <html>
        <body>
            <p>Здравствуйте!</p>
            <p>Для подтверждения email нажмите на кнопку ниже:</p>
            <p><a href="{verification_url}" style="display:inline-block; padding:10px 20px; color:white; background-color:#007bff; text-decoration:none; border-radius:5px;">Подтвердить email</a></p>
            <p>Или скопируйте ссылку в браузер:</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <br>
            <p>Если Вы не отправляли запрос, то игнорируйте это сообщение</p>
            <br>
            <p>С уважением,</p>
            <p><strong>Команда AuthExample</strong></p>
        </body>
    </html>
    """

    subject = "Подтверждение email"
    body = message
    logger.info(f"Письмо для верификации email отправлено на {email}")

    background_tasks.add_task(send_email, email, subject, body)


def send_password_reset_email(
    background_tasks: BackgroundTasks, request: Request, email: EmailStr, token: str
):
    server_url = str(request.base_url).rstrip("/")
    reset_url = f"{server_url}/password/reset?token={token}"

    message = f"""
    <html>
        <body>
            <p>Здравствуйте!</p>
            <p>Чтобы сбросить ваш пароль, нажмите на кнопку ниже:</p>
            <p>
                <a href="{reset_url}" 
                   style="display:inline-block; padding:10px 20px; color:white; 
                          background-color:#007bff; text-decoration:none; border-radius:5px;">
                    Сбросить пароль
                </a>
            </p>
            <p>Или скопируйте ссылку в браузер:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <br>
            <p>Если Вы не отправляли запрос на сброс пароля, просто игнорируйте это письмо.</p>
            <br>
            <p>С уважением,</p>
            <p><strong>Команда AuthExample</strong></p>
        </body>
    </html>
    """

    subject = "Сброс пароля"
    body = message
    logger.info(f"Письмо для сброса пароля отправлено на {email}")

    background_tasks.add_task(send_email, email, subject, body)
