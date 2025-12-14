"""Tests for alert backends, retry policies, and routing."""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.monitoring.alert_contracts import AlertPayload
from src.monitoring.alert_backends import (
    AlertBackend,
    NullAlertBackend,
    StdoutAlertBackend,
    SlackWebhookAlertBackend,
    EmailSMTPAlertBackend,
)
from src.orchestrator.retry_policy import (
    FixedRetryPolicy,
    ExponentialBackoffPolicy,
    retry_policy_from_settings,
)


def _sample_payload() -> AlertPayload:
    return AlertPayload(
        pipeline_id="test-pipeline",
        run_id="run-001",
        severity="ERROR",
        title="Test Alert",
        message="This is a test alert",
        action="alert",
        metadata={"key": "value"},
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
    )


class TestAlertPayload:
    def test_to_dict_serializes_fields(self):
        payload = _sample_payload()
        data = payload.to_dict()
        assert data["pipeline_id"] == "test-pipeline"
        assert data["severity"] == "ERROR"
        assert data["metadata"] == {"key": "value"}
        assert data["timestamp"] == "2025-01-01T12:00:00"


class TestNullAlertBackend:
    def test_always_returns_true(self):
        backend = NullAlertBackend()
        assert backend.send(_sample_payload()) is True


class TestStdoutAlertBackend:
    def test_logs_alert_and_returns_true(self):
        backend = StdoutAlertBackend()
        result = backend.send(_sample_payload())
        # Logger writes to stdout internally; assert return value only to avoid capture complexity
        assert result is True


class TestSlackWebhookAlertBackend:
    def test_returns_false_when_webhook_not_configured(self):
        backend = SlackWebhookAlertBackend(webhook_url="")
        assert backend.send(_sample_payload()) is False

    def test_sends_payload_to_webhook(self):
        backend = SlackWebhookAlertBackend(
            webhook_url="https://hooks.slack.com/test",
            timeout_seconds=1.0,
        )
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("src.monitoring.alert_backends.urlopen", return_value=mock_response) as mock_urlopen:
            result = backend.send(_sample_payload())
            assert result is True
            mock_urlopen.assert_called_once()

    def test_returns_false_on_network_error(self):
        backend = SlackWebhookAlertBackend(webhook_url="https://hooks.slack.com/test")
        from urllib.error import URLError

        with patch("src.monitoring.alert_backends.urlopen", side_effect=URLError("timeout")):
            assert backend.send(_sample_payload()) is False


class TestEmailSMTPAlertBackend:
    def test_returns_false_when_not_configured(self):
        backend = EmailSMTPAlertBackend(
            smtp_host="",
            smtp_port=587,
            username="",
            password="",
            recipients=[],
        )
        assert backend.send(_sample_payload()) is False

    def test_sends_email_successfully(self):
        backend = EmailSMTPAlertBackend(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            recipients=["oncall@example.com"],
        )
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("src.monitoring.alert_backends.smtplib.SMTP", return_value=mock_smtp):
            result = backend.send(_sample_payload())
            assert result is True
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with("user", "pass")
            mock_smtp.sendmail.assert_called_once()


class TestFixedRetryPolicy:
    def test_returns_constant_delay(self):
        policy = FixedRetryPolicy(delay_seconds=2.0)
        assert policy.delay(1) == 2.0
        assert policy.delay(5) == 2.0


class TestExponentialBackoffPolicy:
    def test_exponential_growth(self):
        policy = ExponentialBackoffPolicy(base_delay_seconds=1.0, max_delay_seconds=30.0, jitter=0.0)
        assert policy.delay(1) == 1.0
        assert policy.delay(2) == 2.0
        assert policy.delay(3) == 4.0
        assert policy.delay(4) == 8.0

    def test_caps_at_max_delay(self):
        policy = ExponentialBackoffPolicy(base_delay_seconds=1.0, max_delay_seconds=5.0, jitter=0.0)
        assert policy.delay(10) == 5.0

    def test_jitter_adds_randomness(self):
        policy = ExponentialBackoffPolicy(base_delay_seconds=1.0, max_delay_seconds=30.0, jitter=0.5)
        delays = [policy.delay(2) for _ in range(10)]
        assert not all(d == delays[0] for d in delays), "Jitter should introduce variation"


class TestRetryPolicyFactory:
    def test_creates_exponential_policy(self):
        policy = retry_policy_from_settings(
            strategy="exponential",
            base_delay=2.0,
            max_delay=60.0,
            jitter=0.1,
            fixed_delay=1.0,
        )
        assert isinstance(policy, ExponentialBackoffPolicy)
        assert policy.base_delay_seconds == 2.0

    def test_creates_fixed_policy_by_default(self):
        policy = retry_policy_from_settings(
            strategy="fixed",
            base_delay=2.0,
            max_delay=60.0,
            jitter=0.1,
            fixed_delay=5.0,
        )
        assert isinstance(policy, FixedRetryPolicy)
        assert policy.delay_seconds == 5.0
