"""Persistence utilities for logging LLM automation decisions."""

from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, Optional

from src.agents.contracts import AgentOutput

_LLM_TELEMETRY_PATH = Path("data/telemetry/llm_decisions.jsonl")
_LLM_TELEMETRY_PATH.parent.mkdir(parents=True, exist_ok=True)


def _hash_context(context: Dict[str, object]) -> str:
    payload = json.dumps(context, sort_keys=True, default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def log_llm_decision(
    pipeline_id: str,
    provider: str,
    model: str,
    context: Dict[str, object],
    agent_output: AgentOutput,
    decision: str,
    action_result: Optional[Dict[str, object]] = None,
) -> None:
    """Append an LLM decision record for observability and offline analysis."""

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "pipeline_id": pipeline_id,
        "provider": provider,
        "model": model,
        "decision": decision,
        "context_hash": _hash_context(context),
        "response": agent_output.response.to_dict(),
        "raw_text": agent_output.raw_text,
        "action_result": action_result or {},
    }

    with _LLM_TELEMETRY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
