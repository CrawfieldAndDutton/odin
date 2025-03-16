import smtplib
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from dependencies.configuration import AppConfiguration
from dependencies.logger import logger


class EmailService:
    @staticmethod
    def send_otp_email(email: str, otp: str):

        company_name = "Crawfield and Dutton"
        subject = f"Your {company_name} OTP for Email Verification"

        # Load Jinja2 template
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("otp_email.html")
        # Render template with dynamic data
        email_body = template.render(
            user_name=email.split('@')[0],
            company_name=company_name,
            otp_code=otp,
            otp_expiry=10,  # OTP validity in days
            company_website="https://crawfieldanddutton.com"
        )

        msg = MIMEText(email_body, "html")
        msg['Subject'] = subject
        msg['From'] = AppConfiguration.SMTP_USER
        msg['To'] = email

        # Send email via SMTP
        with smtplib.SMTP(AppConfiguration.SMTP_HOST, AppConfiguration.SMTP_PORT) as server:
            server.starttls()
            server.login(AppConfiguration.SMTP_USER, AppConfiguration.SMTP_PASSWORD)
            server.sendmail(AppConfiguration.SMTP_USER, [email], msg.as_string())

        logger.info(f"OTP email sent successfully to {email}!")
