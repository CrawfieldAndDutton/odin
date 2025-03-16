import smtplib
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader

from dependencies.configuration import AppConfiguration


class EmailService:
    # Initialize Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates/emails'))

    @staticmethod
    def send_otp_email(email: str, otp: str):
        # Get the template
        template = EmailService.env.get_template('registration_otp.html')

        # Render the template with context
        body = template.render(email=email, otp=otp)

        # Create email message
        msg = MIMEText(body, 'html')
        msg['Subject'] = "KYCFabric - Your OTP for Email Verification"
        msg['From'] = AppConfiguration.SMTP_USER
        msg['To'] = email
        msg['Cc'] = AppConfiguration.SMTP_CC_USER

        # Send email
        with smtplib.SMTP(AppConfiguration.SMTP_HOST, AppConfiguration.SMTP_PORT) as server:
            server.starttls()
            server.login(AppConfiguration.SMTP_USER, AppConfiguration.SMTP_PASSWORD)
            server.sendmail(AppConfiguration.SMTP_USER, [email], msg.as_string())

    @staticmethod
    def send_contact_us_lead_email(name: str, lead_email: str, company: str, phone: str, message: str):
        # Get the template
        template = EmailService.env.get_template('contact_us_lead.html')

        # Render the template with context
        body = template.render(name=name, lead_email=lead_email, company=company, phone=phone, message=message)

        # Create email message
        msg = MIMEText(body, 'html')
        msg['Subject'] = "KYCFabric - Contact Us Lead Details"
        msg['From'] = AppConfiguration.SMTP_USER
        msg['To'] = AppConfiguration.SMTP_CC_USER

        # Send email
        with smtplib.SMTP(AppConfiguration.SMTP_HOST, AppConfiguration.SMTP_PORT) as server:
            server.starttls()
            server.login(AppConfiguration.SMTP_USER, AppConfiguration.SMTP_PASSWORD)
            server.sendmail(AppConfiguration.SMTP_USER, [AppConfiguration.SMTP_CC_USER], msg.as_string())
