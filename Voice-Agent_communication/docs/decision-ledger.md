# Decision Ledger

The decision ledger captures every AI automation verdict emitted by the orchestration pipeline. Each record is append-only and generated immediately after the decision gate evaluates the MCP + ML context.

## Storage

- Backend uses `sqlmodel` with an async SQLite database by default (`DATABASE_URL` in `.env`).
- Table name: `decision_ledger`.

## Columns

| Field | Type | Description |
| ----- | ---- | ----------- |
| `decision_id` | UUID | Primary key for the decision event. |
| `timestamp` | UTC datetime | Server timestamp when the event was persisted. |
| `provider` | Text | Upstream LLM provider identifier. |
| `model` | Text | Model name or version. |
| `prompt_hash` | Text | Deterministic hash of the prompt contract. |
| `schema_version` | Text | Contract version captured by the ledger service. |
| `ml_risk_score` | Real | Normalized ML risk score (0-1). |
| `llm_confidence` | Real nullable | Normalized LLM confidence (0-1). |
| `gate_verdict` | Text | `allow` or `block`. |
| `gate_reason` | Text | Deterministic reason code from the decision gate. |
| `action_type` | Text nullable | Recommended action label. |
| `action_params` | Text nullable | JSON-serialized parameters for the recommended action. |
| `schema_valid` | Boolean | Flag indicating whether the MCP payload passed schema validation. |

## Lifecycle

1. MCP agent responds with an `LLMDecision` payload.
2. `DecisionGate` evaluates the payload plus ML risk score.
3. `AudioPipelineService` constructs a `DecisionGatePayload`, attaches the deterministic `prompt_hash`, and records both payloads via `DecisionLedger.record_event`.
4. The ledger persists the event using an async session and immediately commits, after which telemetry emits the verdict.

## Query Examples

```sql
-- Count blocks by reason
SELECT gate_reason, COUNT(*)
FROM decision_ledger
GROUP BY gate_reason
ORDER BY COUNT(*) DESC;

-- Confidence calibration bucketed by provider
SELECT provider,
       ROUND(llm_confidence, 1) AS bucket,
       COUNT(*)
FROM decision_ledger
WHERE llm_confidence IS NOT NULL
GROUP BY provider, bucket
ORDER BY provider, bucket;
```

## Future Extensions

- Add outcome fields (success/failure) for closed-loop evaluation.
- Emit telemetry events alongside persistence for real-time monitoring.
- Support pluggable storage backends (e.g., PostgreSQL) via configuration.
- Use the backfill script `python -m app.scripts.backfill_prompt_hash` to assign fallback hashes for legacy rows.
