from __future__ import annotations

import csv
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from flask import current_app


def mail_is_configured() -> bool:
    return bool(current_app.config.get("SMTP_HOST"))


def send_email(subject: str, recipients: Iterable[str], text_body: str, html_body: str | None = None) -> bool:
    recipients = [recipient for recipient in recipients if recipient]
    if not recipients or not mail_is_configured():
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = ", ".join(recipients)
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(current_app.config["SMTP_HOST"], current_app.config["SMTP_PORT"], timeout=30) as smtp:
        if current_app.config.get("SMTP_USE_TLS", True):
            smtp.starttls()
        username = current_app.config.get("SMTP_USERNAME")
        password = current_app.config.get("SMTP_PASSWORD")
        if username:
            smtp.login(username, password or "")
        smtp.send_message(message)
    return True


def ensure_exports_dir() -> Path:
    exports_dir = Path(current_app.config["EXPORTS_DIR"])
    if not exports_dir.is_absolute():
        exports_dir = Path(current_app.root_path) / exports_dir
    exports_dir.mkdir(parents=True, exist_ok=True)
    return exports_dir


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(rows)
