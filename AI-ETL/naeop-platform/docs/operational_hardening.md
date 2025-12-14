# Operational Hardening Design

## Goal
Extend the autonomous remediation loop delivered in v0.2.0 with production-grade alerting, retry, and routing controls without altering the frozen intelligence contract. The new work must be opt-in, configuration-driven, and backward compatible with existing tests.

## Scope
- Alert delivery backends for Slack webhook and SMTP email, selectable via configuration.
- Retry policy abstraction supporting exponential backoff with jitter for autonomous remediation retries and baseline executor retries.
- Configurable action routing so each remediation directive (retry, skip, alert, tune, none) can target specific backends or policies.
- Telemetry enrichment to capture alert delivery outcomes and retry attempts.
- Test coverage for new backends, retry policy, and end-to-end remediation flow using both slack and email mocks.

Out of scope: dashboards, managed queueing systems, new remediation action types, or changes to the LLM/decision contracts.

## Components
- **AlertBackend interface** in [src/monitoring/alerts.py](../src/monitoring/alerts.py) with implementations:
  - SlackWebhookAlertBackend: POST to a configured webhook, lightweight timeout handling, redact secrets in logs.
  - EmailSMTPAlertBackend: Send email via SMTP with TLS support; use dependency injection to allow mocking.
  - StdoutAlertBackend: existing logger-based fallback for local/dev use.
- **RetryPolicy abstraction** in [src/orchestrator/executor.py](../src/orchestrator/executor.py) or a dedicated module, encapsulating retries with strategies (fixed, exponential, capped). Default remains current fixed delay to preserve behavior when policy not configured.
- **ActionRouter** helper inside [src/orchestrator/remediation.py](../src/orchestrator/remediation.py) to resolve which alert backend or retry policy applies to each action based on configuration.
- **Settings additions** in [src/config/settings.py](../src/config/settings.py) for alert targets, webhook URLs, SMTP credentials, retry strategy, and per-action routing rules. All new fields require sane defaults to maintain compatibility.

## Configuration Model
```
remediation:
  alert:
    backend: slack
    slack:
      webhook_url: ${SLACK_WEBHOOK_URL}
      timeout_seconds: 5
    email:
      enabled: false
      smtp_host: smtp.example.com
      smtp_port: 587
      username: ${SMTP_USERNAME}
      password: ${SMTP_PASSWORD}
      recipients:
        - oncall@example.com
  retry:
    strategy: exponential
    max_attempts: 3
    base_delay_seconds: 2
    max_delay_seconds: 30
    jitter: 0.25
```

Configuration is loaded via Settings.from_env and injected into Executor, AlertManager, and RemediationExecutor on construction.

## Telemetry Updates
- Extend [src/monitoring/llm_telemetry.py](../src/monitoring/llm_telemetry.py) to include `alert_backend`, `alert_status`, and `retry_policy` fields when actions occur.
- Append retry attempts and delays to [src/monitoring/telemetry_schema.py](../src/monitoring/telemetry_schema.py) events for downstream analytics.

## Testing Strategy
- Unit tests for Slack and Email backends with mocked network/email clients covering success, timeout, and error paths.
- RetryPolicy tests verifying delay sequences, jitter bounds, and max attempt enforcement.
- Integration test extending [src/tests/test_remediation_flow.py](../src/tests/test_remediation_flow.py) to validate retry backoff behavior and alert routing to Slack mock backend.
- Configuration round-trip tests ensuring Settings defaults maintain current behavior when new settings are absent.

## Rollout Plan
1. Implement AlertBackend interface and concrete backends with feature-flagged configuration.
2. Introduce RetryPolicy abstraction and integrate with Executor and remediation retry path.
3. Add ActionRouter and update RemediationExecutor to honor routing.
4. Update telemetry and metrics.
5. Add tests incrementally and run full pytest suite.
6. Document new configuration in README and architecture docs.

## Risks and Mitigations
- **External dependency failures**: wrap network/email operations with timeouts and fail-safe fallbacks to Stdout backend.
- **Configuration mistakes**: validate critical settings (webhook URL format, SMTP host/port) during startup and log actionable errors.
- **Telemetry size growth**: ensure additional fields remain lightweight strings/ints to avoid bloating JSONL records.

Completion of this plan produces a hardened Phase 2.1 release ready for real operational environments and prepares the groundwork for RL signal quality in Phase 3.
