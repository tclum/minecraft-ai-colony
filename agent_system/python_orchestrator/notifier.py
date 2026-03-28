import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from .config import SHARED_DIR

ALERT_LOG_FILE = SHARED_DIR / "alert_log.md"

def send_email_alert(subject: str, body: str):
    sender = os.getenv("ALERT_EMAIL", "")
    password = os.getenv("ALERT_EMAIL_PASSWORD", "")

    if not sender or not password:
        print("[notifier] No email credentials found in .env — skipping email alert.")
        _write_alert_log(subject, body)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Tim Agent] {subject}"
    msg["From"] = sender
    msg["To"] = sender

    text_body = f"{body}\n\nTimestamp: {datetime.now().isoformat()}"
    html_body = f"""
    <html><body>
    <h2>🤖 Tim Agent Alert</h2>
    <p>{body.replace(chr(10), '<br>')}</p>
    <hr>
    <small>Timestamp: {datetime.now().isoformat()}</small>
    </body></html>
    """

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, sender, msg.as_string())
        print(f"[notifier] Alert email sent: {subject}")
    except Exception as e:
        print(f"[notifier] Failed to send email: {e}")

    _write_alert_log(subject, body)

def _write_alert_log(subject: str, body: str):
    timestamp = datetime.now().isoformat()
    entry = f"\n## {timestamp}\n**{subject}**\n{body}\n"
    with open(ALERT_LOG_FILE, "a") as f:
        f.write(entry)