import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

#SMTP setup

def send_reset_email(to_email: str, reset_token: str):
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = "Password reset request"

    body = f"""\
Hi,
Click the below link to reset your password,

http://localhost:8000/auth/reset-password?token={reset_token}

If you did not request this, please ignore this email.
"""

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
    except Exception as e:
        print("Email sending failed:", e)
        raise 
