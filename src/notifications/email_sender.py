import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import (
    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
)


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(
    recipient,
    subject,
    html,
):

    message = MIMEMultipart("alternative")

    message["Subject"] = subject
    message["From"] = EMAIL_ADDRESS
    message["To"] = recipient

    message.attach(
        MIMEText(
            html,
            "html",
        )
    )

    with smtplib.SMTP(
        SMTP_SERVER,
        SMTP_PORT,
    ) as server:

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD,
        )

        server.sendmail(
            EMAIL_ADDRESS,
            recipient,
            message.as_string(),
        )

    print("Email sent successfully.")