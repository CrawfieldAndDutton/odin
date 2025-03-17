import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dependencies.configuration import AppConfiguration
from jinja2 import Environment, FileSystemLoader


class EmailService:
    @staticmethod
    def render_template(template_name: str, **kwargs) -> str:
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template(template_name)
        return template.render(**kwargs)

    def send_otp_email(self, email: str, otp: str):
        subject = "Your OTP for Email Verification"
        email_body = self.render_template("otp_template.html", email=email, otp=otp)

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = AppConfiguration.SMTP_USER
        msg['To'] = email
        msg.attach(MIMEText(email_body, 'html'))

        with smtplib.SMTP(AppConfiguration.SMTP_HOST, AppConfiguration.SMTP_PORT) as server:
            server.starttls()
            server.login(AppConfiguration.SMTP_USER, AppConfiguration.SMTP_PASSWORD)
            server.sendmail(AppConfiguration.SMTP_USER, [email], msg.as_string())
