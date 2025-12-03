import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from config.config import settings 
import logging
from pathlib import Path

logger = logging.getLogger("mail")

class MailService:
    def __init__(self):
        template_path = Path("app/templates/emails")
        if not template_path.exists():
            logger.warning(f"Template path not found: {template_path.resolve()}")
        self.env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=select_autoescape(["html", "xml"])
        )

    async def send_mail(
        self,
        to: str | list[str],
        subject: str,
        template_name: str | None = None,
        context: dict | None = None,
        body: str | None = None,
        html_body: str | None = None,
        is_html: bool = True,
    ):
        """
        Send email using SMTP (async).
        Priority:
            1. If `html_body` provided → use that as HTML
            2. Else if `template_name` provided → render template
            3. Else use `body` (plain text or html depending on `is_html`)
        """
        try:
            message = MIMEMultipart("alternative")
            message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.SYSTEM_ADMIN_EMAIL}>"
            message["To"] = ", ".join(to) if isinstance(to, list) else to
            message["Subject"] = subject

            text_part = None
            html_part = None

            # --- Template rendering ---
            if template_name:
                try:
                    template = self.env.get_template(template_name)
                    rendered_html = template.render(**(context or {}))
                    html_part = MIMEText(rendered_html, "html")
                except TemplateNotFound:
                    logger.error(f"Template '{template_name}' not found. Falling back to plain text.")
                    html_part = None

            # ---  Explicit HTML body ---
            elif html_body:
                html_part = MIMEText(html_body, "html")

            # --- plain text fallback ---
            if body:
                text_part = MIMEText(body, "plain" if not is_html else "html")

            # --- Attach parts ---
            if text_part:
                message.attach(text_part)
            if html_part and is_html:
                message.attach(html_part)

            # --- Send ---
            await aiosmtplib.send(
                message,
                hostname=settings.HOST,
                port=settings.MAIL_PORT,
                username=settings.USERNAME,
                password=settings.PASSWORD,
                start_tls=settings.MAIL_USE_TLS,
                use_tls=settings.MAIL_USE_SSL,
                timeout=15,
            )

            logger.info(f"Email sent successfully to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False


# global instance
mail = MailService()
