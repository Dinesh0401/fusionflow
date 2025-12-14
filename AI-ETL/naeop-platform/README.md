# NeuroAdaptive ETL Orchestration Platform (NAEOP)

## Overview
The NeuroAdaptive ETL Orchestration Platform (NAEOP) is an intelligent ETL control plane that now completes the full loop from prediction to remediation. It orchestrates data pipelines, anticipates failures, reasons about recovery options through a contracted LLM agent, executes safe automation, and records every decision for audit.

## Intelligent Remediation Loop
1. Telemetry and model features anticipate failures before they surface.
2. A contracted LLM agent analyzes the situation and returns a structured action plan.
3. Policy gating via the decision engine ensures only compliant automations run.
4. The remediation executor performs concrete actions (retry, skip, alert, tune placeholder) against the live pipeline.
5. Metrics and JSONL telemetry capture decision, action, and outcome for replay and learning.

## Architecture
```
             ┌────────────────────────┐
             │ Data Pipelines (DAGs) │
             └────────────┬──────────┘
                          │
     ┌────────────────────▼────────────────────┐
     │ Executor                               │
     │  • runs tasks & records status          │
     │  • calls failure predictor              │
     │  • invokes automation agent             │
     └──────────────────┬──────────────────────┘
                        │
        ┌───────────────▼────────────────┐
        │ Decision Engine                │
        │  • risk & confidence thresholds│
        │  • optional human-in-loop      │
        └───────────────┬────────────────┘
                        │execute/block
        ┌───────────────▼────────────────┐
        │ Remediation Executor           │
        │  • retry / skip / alert / tune │
        │  • publishes results           │
        └───────────────┬────────────────┘
                        │
       ┌────────────────▼─────────────────┐
       │ Telemetry & Metrics              │
       │  • CSV pipeline telemetry        │
       │  • JSONL LLM decision history    │
       └──────────────────────────────────┘
```

Key modules: [src/orchestrator/executor.py](src/orchestrator/executor.py), [src/orchestrator/remediation.py](src/orchestrator/remediation.py), [src/orchestrator/decision_engine.py](src/orchestrator/decision_engine.py), [src/monitoring/llm_telemetry.py](src/monitoring/llm_telemetry.py), [src/agents/contracts.py](src/agents/contracts.py).

## Why This Platform Is Different
- Deterministic agent contracts enforce safe, provider-agnostic LLM usage across OpenAI, Ollama, and Hugging Face backends.
- Policy-driven verdicts ensure automation only proceeds when risk and confidence thresholds are satisfied.
- Remediation translates recommendations into concrete retries, skips, and alerts with direct executor hooks.
- Every automation run emits auditable JSONL telemetry linking decision, action, and outcome for future analysis.
- Complete pytest coverage demonstrates failure injection, recovery, and trace logging.

## Execution Flow Walkthrough (Failure → Recovery)
1. Inject a synthetic task failure inside a DAG.
2. Failure telemetry raises the predicted risk above the configured threshold.
3. The LLM agent produces a structured plan recommending a retry with high confidence.
4. The decision engine authorizes the plan (verdict: execute) because risk is high and confidence exceeds the floor.
5. The remediation executor retries the failed task, marks it completed, and persists a JSONL record of the success.

See [src/tests/test_remediation_flow.py](src/tests/test_remediation_flow.py) for the end-to-end pytest that exercises this scenario.

### Example Run
```
python -m pytest src/tests/test_remediation_flow.py -q

tests/test_remediation_flow.py .                                 [100%]
1 passed in 3.12s
```
Inspect the generated telemetry at `data/telemetry/llm_decisions.jsonl` to review the recorded decision, recommended action, and final outcome.

## Quickstart
1. Install dependencies:
   ```
   git clone https://github.com/Dinesh0401/fusionflow.git
   cd fusionflow/naeop-platform
   pip install -r requirements.txt
   ```
2. Run the sample pipeline:
   ```
   python src/main.py
   ```
3. Optional: configure an external LLM provider (defaults to deterministic mock):
   ```
   setx LLM_AGENT_PROVIDER openai
   setx OPENAI_API_KEY <your-api-key>
   ```
   Additional environment variables: LLM_AGENT_MODEL, LLM_AGENT_TEMPERATURE, LLM_AGENT_MAX_TOKENS, LLM_AGENT_ENABLED.

## Telemetry and Observability
- Pipeline metrics and historical runs are persisted via [src/monitoring/telemetry_schema.py](src/monitoring/telemetry_schema.py).
- LLM automation telemetry, including remediation outcomes, is written to `data/telemetry/llm_decisions.jsonl` through [src/monitoring/llm_telemetry.py](src/monitoring/llm_telemetry.py).
- Metrics counters and timers are available through [src/monitoring/metrics.py](src/monitoring/metrics.py).

## Project Structure
```
naeop-platform
├── src
│   ├── main.py
│   ├── adapters/
│   ├── agents/
│   ├── config/
│   ├── core/
│   ├── ml/
│   ├── monitoring/
│   ├── orchestrator/
│   ├── pipelines/
│   └── tests/
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Contributing
Contributions are welcome. Please open an issue or submit a pull request for enhancements or fixes.

## License
This project is licensed under the MIT License. See LICENSE for details.