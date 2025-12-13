"""Alerting helpers."""

from typing import Optional

from src.core.logger import get_logger


class AlertManager:
    def __init__(self, threshold: Optional[float] = None, logger_name: str = "AlertManager"):
        self.threshold = threshold
        self.logger = get_logger(logger_name)

    def check_alert(self, metric_value: float) -> None:
        if self.threshold is not None and metric_value > self.threshold:
            self.trigger_alert(f"Metric value {metric_value} exceeded threshold {self.threshold}")

    def trigger_alert(self, message: str) -> None:
        self.logger.warning("ALERT: %s", message)
        # Extend here with email, Slack, or PagerDuty integrations.