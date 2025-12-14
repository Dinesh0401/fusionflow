# NAEOP Autonomous Remediation Architecture

## Context
NAEOP now operates a closed-loop intelligence cycle that spans risk prediction, structured reasoning, policy approval, concrete remediation, and full telemetry capture. This document explains how decisions are made and governed so that contributors can extend the system without breaking safety guarantees.

## Core Components
- **Executor** – Orchestrates DAG execution, tracks task status, surfaces failures, and coordinates downstream automation. Implemented in [src/orchestrator/executor.py](../src/orchestrator/executor.py).
- **Failure Predictor** – Scores upcoming tasks using historical telemetry to estimate failure risk, enabling proactive interventions. Implemented in [src/ml/failure_model.py](../src/ml/failure_model.py).
- **LLM Agent** – Produces structured remediation advice via deterministic contracts, regardless of backing provider. Contracts live in [src/agents/contracts.py](../src/agents/contracts.py) and pluggable agents in [src/agents/llm_agent.py](../src/agents/llm_agent.py).
- **Decision Engine** – Applies policy thresholds for risk and LLM confidence, optionally forcing human approval. See [src/orchestrator/decision_engine.py](../src/orchestrator/decision_engine.py).
- **Remediation Executor** – Maps approved agent directives into concrete actions (retry, skip, alert, tune placeholder) with consistent result payloads. Defined in [src/orchestrator/remediation.py](../src/orchestrator/remediation.py).
- **Telemetry Layer** – Persists CSV pipeline telemetry plus JSONL LLM decision traces for audit and learning. Implemented in [src/monitoring/telemetry_schema.py](../src/monitoring/telemetry_schema.py) and [src/monitoring/llm_telemetry.py](../src/monitoring/llm_telemetry.py).

## Decision Flow
```
1. Executor records task context and failure signals.
2. Failure predictor emits ml_failure_risk.
3. LLM agent receives structured context and responds with action + confidence.
4. Decision engine evaluates:
   • if risk < threshold → execute (no automation)
   • if LLM missing or confidence < floor → request human / block
   • else → verdict execute
5. Remediation executor performs the approved action and reports status.
6. Telemetry logger appends decision, action_result, and hashes of context.
```

## Policy Configuration
- **ML risk threshold** – Minimum probability before automation is considered. Prevents unnecessary interventions for low-risk anomalies.
- **LLM confidence threshold** – Minimum agent certainty required for autonomous action. Sub-threshold recommendations are diverted to humans when available.
- **Human-in-loop switch** – Forces `request_human` verdict instead of hard blocking when policy demands oversight.

Policies are sourced from configuration and injected into the decision engine at executor construction time, ensuring the same logic applies to every pipeline run.

## Remediation Actions
| Action | Trigger | Outcome |
| ------ | ------- | ------- |
| retry | LLM recommends rerun and policy approves | Executor retries the failed task immediately and records success/failure. |
| skip | Agent requests bypass | Task state set to skipped with downstream context nulled. |
| alert | Agent escalates issue | Alert manager dispatches notification with agent rationale. |
| tune | Placeholder | Logged as manual follow-up until automated tuning is implemented. |
| none | No action | System records that no remediation was required. |

Each action produces a standardized result dict capturing `action`, `status`, and `detail`, enabling downstream analytics without bespoke parsing.

## Telemetry and Audit Trail
- CSV telemetry tracks DAG-level metrics, execution durations, and failure counts for model training.
- JSONL decision logs (default path `data/telemetry/llm_decisions.jsonl`) capture:
  - Timestamp, pipeline ID, provider, and model.
  - Risk verdict, structured agent response, raw text for audit, and remediation outcome.
  - Context hash rather than raw payload to protect sensitive data while enabling correlation.

These records are the foundation for future learning-based optimization (reward modeling, RL) without rerunning production incidents.

## System Walkthrough
1. A DAG task raises an exception and the executor records `latest_error` in context.
2. The failure predictor scores the incident above the configured risk threshold.
3. The contracted LLM agent returns `recommended_action=retry` with high confidence.
4. Decision engine checks risk and confidence; verdict becomes `execute` (automation allowed).
5. Remediation executor retries the task via executor hooks, succeeds, and reports `status=succeeded`.
6. Telemetry logger writes a JSONL entry linking decision, action, and outcome for audit.

Refer to [src/tests/test_remediation_flow.py](../src/tests/test_remediation_flow.py) for the canonical integration test validating this flow end to end.

## Validation Checklist
- `python -m pytest` → All fifteen tests pass, including remediation scenarios.
- Telemetry file `data/telemetry/llm_decisions.jsonl` grows with each automated decision.
- Alert manager integrations are optional; absence does not break remediation paths.

## Release Tagging
The autonomous remediation loop completes Phase 2 of the roadmap. Tag the repository as `v0.2.0-autonomous-remediation` once documentation is merged and tests pass to signify this milestone.
