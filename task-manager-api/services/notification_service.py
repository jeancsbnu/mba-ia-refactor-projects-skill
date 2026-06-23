import smtplib
import os
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.email_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.email_port = int(os.environ.get('SMTP_PORT', 587))
        self.email_user = os.environ.get('SMTP_USER', '')
        self.email_password = os.environ.get('SMTP_PASS', '')

    def send_email(self, to, subject, body):
        if not self.email_user or not self.email_password:
            logger.warning("SMTP não configurado; email não enviado para %s", to)
            return False
        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, to, f"Subject: {subject}\n\n{body}")
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except Exception:
            logger.error("Erro ao enviar email para %s", to, exc_info=True)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self.send_email(user.email, subject, body)
