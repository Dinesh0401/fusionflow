# LLM Decision Contract

All large language model outputs consumed by the backend must follow this deterministic contract.

## JSON Structure

```json
{
  "risk_summary": "string",
  "likely_root_cause": "string",
  "confidence": 0.0,
  "recommended_action": {
    "type": "retry | tune | skip | alert",
    "parameters": {}
  },
  "provider": "string",
  "model": "string",
  "prompt_hash": "string"
}
```

## Validation Rules

- `confidence` is a float ∈ [0, 1] and is rounded to four decimal places on ingest.
- `recommended_action.type` must be one of `retry`, `tune`, `skip`, or `alert`.
- `recommended_action.parameters` allows provider-specific execution hints.
- `prompt_hash` is a deterministic digest of the prompt context for audit trails.

## Usage

- Backend validates responses via `app.schemas.llm.LLMDecision`.
- Invalid payloads are logged and ignored to preserve graceful degradation.
- Frontend renders decisions from the session store for operator review.
