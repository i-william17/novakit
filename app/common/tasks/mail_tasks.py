from app.core.celery_app import celery
from app.core.mailer import mail
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True, name="app.tasks.send_mail", acks_late=True)
def send_mail_task(self, to, subject, template_name=None, context=None, body=None, html_body=None, is_html=True):
    """Celery task to send email (sync wrapper around async mail.send_mail)."""
    try:
        # if mail.send_mail is async, run it with asyncio
        import asyncio
        coro = mail.send_mail(
            to=to,
            subject=subject,
            template_name=template_name,
            context=context,
            body=body,
            html_body=html_body,
            is_html=is_html,
        )
        # run coroutine in worker
        asyncio.run(coro)
        logger.info(f"send_mail_task: email to {to} sent")
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.exception("send_mail_task failed")
        # will be retried according to Celery config (max_retries)
        raise self.retry(exc=exc, countdown=60)
