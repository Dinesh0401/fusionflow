"""Alert backend abstractions for routing incident notifications."""

from __future__ import annotations

import json
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from typing import List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from src.core.logger import get_logger
from src.monitoring.alert_contracts import AlertPayload


class AlertBackend(ABC):
    """Interface for delivering alerts to external systems."""

    @abstractmethod
    def send(self, payload: AlertPayload) -> bool:
        """Deliver the alert.

        Implementations must swallow their own exceptions and return False on failure
        so remediation flows remain resilient.
        """

        raise NotImplementedError


class NullAlertBackend(AlertBackend):
    """Default no-op backend used when alerting is disabled."""

    def send(self, payload: AlertPayload) -> bool:  # pragma: no cover - trivial
        return True


class StdoutAlertBackend(AlertBackend):
    """Log alerts to stdout via the platform logger."""

    def __init__(self, logger_name: str = "AlertBackend") -> None:
        self.logger = get_logger(logger_name)

    def send(self, payload: AlertPayload) -> bool:
        self.logger.warning(
            "ALERT [%s] %s: %s",
            payload.severity,
            payload.title,
            payload.message,
        )
        return True


class SlackWebhookAlertBackend(AlertBackend):
    """Send alerts to a Slack channel via incoming webhook."""

    def __init__(self, webhook_url: str, timeout_seconds: float = 5.0) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout_seconds
        self.logger = get_logger("SlackAlertBackend")

    def send(self, payload: AlertPayload) -> bool:
        if not self.webhook_url:
            self.logger.warning("Slack webhook URL not configured; alert not sent")
            return False

        body = {
            "text": f"*[{payload.severity}] {payload.title}*\n{payload.message}",
            "attachments": [
                {
                    "color": self._severity_color(payload.severity),
                    "fields": [
                        {"title": "Pipeline", "value": payload.pipeline_id, "short": True},
                        {"title": "Run", "value": payload.run_id, "short": True},
                        {"title": "Action", "value": payload.action, "short": True},
                    ],
                }
            ],
        }

        try:
            req = Request(
                self.webhook_url,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=self.timeout) as resp:
                return resp.status == 200
        except (URLError, OSError) as exc:
            self.logger.error("Slack alert delivery failed: %s", exc)
            return False

    @staticmethod
    def _severity_color(severity: str) -> str:
        return {
            "INFO": "#36a64f",
            "WARNING": "#ffcc00",
            "ERROR": "#ff6600",
            "CRITICAL": "#ff0000",
        }.get(severity.upper(), "#cccccc")


class EmailSMTPAlertBackend(AlertBackend):
    """Send alerts via SMTP email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        recipients: List[str],
        sender: Optional[str] = None,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = recipients
        self.sender = sender or username
        self.logger = get_logger("EmailAlertBackend")

    def send(self, payload: AlertPayload) -> bool:
        if not self.smtp_host or not self.recipients:
            self.logger.warning("Email SMTP not configured; alert not sent")
            return False

        subject = f"[{payload.severity}] {payload.title}"
        body = (
            f"Pipeline: {payload.pipeline_id}\n"
            f"Run: {payload.run_id}\n"
            f"Action: {payload.action}\n\n"
            f"{payload.message}"
        )

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.sender, self.recipients, msg.as_string())
            return True
        except smtplib.SMTPException as exc:
            self.logger.error("Email alert delivery failed: %s", exc)
            return False
