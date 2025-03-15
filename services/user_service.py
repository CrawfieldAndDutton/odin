import smtplib
from email.mime.text import MIMEText
from dependencies.configuration import AppConfiguration


class EmailService:
    @staticmethod
    def send_otp_email(email: str, otp: str):
        subject = "Your OTP for Email Verification"
        body = f"Your OTP is: {otp}"
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = AppConfiguration.SMTP_USER
        msg['To'] = email

        with smtplib.SMTP(AppConfiguration.SMTP_HOST, AppConfiguration.SMTP_PORT) as server:
            server.starttls()
            server.login(AppConfiguration.SMTP_USER, AppConfiguration.SMTP_PASSWORD)
            server.sendmail(AppConfiguration.SMTP_USER, [email], msg.as_string())
