from app.core.celery_app import celery_app
from app.core.mailer import mail
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.send_email_task", max_retries=3)
def send_email_task(self, to: str, name: str):
    """Celery task to send email via RabbitMQ queue."""
    try:
        result = mail.send_mail_sync(  # use sync variant for Celery worker
            to=to,
            subject="Queued Email from Celery",
            template_name="test_mail.html",
            context={"name": name},
        )
        logger.info(f"Email sent to {to}")
        return {"status": "sent", "to": to}
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise self.retry(exc=e, countdown=5)
