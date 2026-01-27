import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_USERNAME = os.environ["SOURCE_EMAIL"]
SMTP_PASSWORD = "*******************"

FROM_EMAIL = SMTP_USERNAME


def send_email(to_email: str, subject: str, message: str):

    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(message, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


def handler(event, context):
    for record in event.get("Records", []):
        try:
            payload = json.loads(record["body"])
        except json.JSONDecodeError:
            print(f"Invalid JSON body: {record['body']}")
            continue

        to_email = payload.get("email")
        subject = payload.get("subject")
        message = payload.get("message")

        if not to_email or not subject or not message:
            print(f"Missing email/subject/message in payload: {payload}")
            continue

        try:
            send_email(to_email, subject, message)
            print(f"Email sent to {to_email} with subject '{subject}'")
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")

    return {"status": "processed"}
