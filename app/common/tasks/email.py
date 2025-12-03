from app.core.celery_app import celery
import smtplib

@celery.task(bind=True, max_retries=3)
def send_email(self, to: str, subject: str, body: str):
    try:
        # example SMTP logic here
        print(f"Sending email to {to} - {subject}")
        # smtp logic...
        return {"status": "success"}
    except Exception as e:
        self.retry(exc=e, countdown=10)
