"""LLM-backed automation agents used in Phase-3 orchestration."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from src.agents.contracts import AgentOutput, LLMRecommendedAction, LLMResponse

LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore
    OPENAI_AVAILABLE = False


@dataclass
class AgentConfig:
    """Configuration for LLM driven agents."""

    enabled: bool = True
    provider: str = "mock"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_output_tokens: int = 512
    api_key_env: str = "OPENAI_API_KEY"
    endpoint: Optional[str] = None
    system_prompt: str = (
        "You are an ETL reliability assistant. "
        "Return structured JSON that matches the provided schema and avoids extra prose."
    )
    fallback_message: str = (
        "LLM support unavailable. Use mock playbook generated from telemetry instead."
    )


class BaseAgent:
    """Simplified agent protocol returning structured agent output."""

    def generate_action_plan(self, context: Dict[str, Any]) -> AgentOutput:  # pragma: no cover - interface only
        raise NotImplementedError


class MockAgent(BaseAgent):
    """Deterministic agent used for local testing and CI."""

    def generate_action_plan(self, context: Dict[str, Any]) -> AgentOutput:
        pipeline = context.get("pipeline_id", "unknown pipeline")
        latest_error = context.get("latest_error") or "n/a"
        failed_tasks = context.get("failed_tasks", [])
        risk = context.get("predicted_risk")
        risk_text = f"{risk:.2f}" if isinstance(risk, (int, float)) else "n/a"

        steps = [
            f"Inspect telemetry logs for {pipeline} (risk={risk_text}).",
        ]
        if failed_tasks:
            steps.append(f"Retry or debug affected tasks: {', '.join(failed_tasks)}.")
        else:
            steps.append("Validate upstream dependencies and data freshness.")
        steps.append(f"Primary error context: {latest_error}.")
        plan_text = "\n".join(f"- {line}" for line in steps)

        response = LLMResponse(
            risk_summary=f"Risk assessment for {pipeline}: {risk_text}",
            likely_root_cause=latest_error,
            confidence=0.5,
            recommended_action=LLMRecommendedAction(
                type="alert",
                parameters={"detail": latest_error or "analysis unavailable"},
            ),
        )

        return AgentOutput(response=response, raw_text=json.dumps(response.to_dict()))


class LLMAgent(BaseAgent):
    """Thin wrapper on top of optional LLM providers with graceful fallback."""

    def __init__(self, config: AgentConfig, fallback: Optional[BaseAgent] = None) -> None:
        self.config = config
        self.fallback = fallback or MockAgent()
        self.provider = self.config.provider.lower()
        self._client = self._build_client()

    def _build_client(self):  # pragma: no cover - exercised indirectly
        if not self.config.enabled or self.provider != "openai":
            return None
        if not OPENAI_AVAILABLE:
            LOGGER.warning("OpenAI SDK not installed; reverting to mock agent")
            return None
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            LOGGER.warning("Environment variable %s missing; reverting to mock agent", self.config.api_key_env)
            return None
        try:
            return OpenAI(api_key=api_key)
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Failed to initialise OpenAI client: %s", exc)
            return None

    def generate_action_plan(self, context: Dict[str, Any]) -> AgentOutput:
        prompt = self._build_prompt(context)

        if self.provider == "openai":
            if not self._client:
                return self.fallback.generate_action_plan(context)
            try:
                response = self._client.responses.create(  # type: ignore[call-arg]
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_output_tokens,
                    input=[
                        {
                            "role": "system",
                            "content": self.config.system_prompt,
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                )
            except Exception as exc:  # pragma: no cover - network errors
                LOGGER.error("LLM request failed: %s", exc)
                return self.fallback.generate_action_plan({**context, "error": str(exc)})

            message = getattr(response, "output_text", None) or self._unwrap_output(response)
            if not message:
                return self.fallback.generate_action_plan(context)
            return self._parse_structured_response(message, context)

        if self.provider == "ollama":
            message = self._call_ollama(prompt)
            if message:
                return self._parse_structured_response(message, context)
            return self.fallback.generate_action_plan(context)

        if self.provider == "huggingface":
            message = self._call_huggingface(prompt)
            if message:
                return self._parse_structured_response(message, context)
            return self.fallback.generate_action_plan(context)

        return self.fallback.generate_action_plan(context)

    def _call_ollama(self, prompt: str) -> Optional[str]:  # pragma: no cover - runtime integration
        endpoint = self.config.endpoint or "http://localhost:11434/api/generate"
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_output_tokens,
            },
        }
        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            LOGGER.error("LLM request failed (ollama): %s", exc)
            return None

        data = response.json()
        message = data.get("response")
        if not message and isinstance(data.get("message"), dict):
            message = data["message"].get("content")
        if not message and isinstance(data.get("messages"), list):
            contents = [item.get("content") for item in data["messages"] if isinstance(item, dict)]
            message = "\n".join([text for text in contents if isinstance(text, str)])
        return message.strip() if isinstance(message, str) else None

    def _call_huggingface(self, prompt: str) -> Optional[str]:  # pragma: no cover - runtime integration
        token = os.getenv(self.config.api_key_env)
        if not token:
            LOGGER.warning("Environment variable %s missing; reverting to mock agent", self.config.api_key_env)
            return None
        endpoint = self.config.endpoint or f"https://api-inference.huggingface.co/models/{self.config.model}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        payload: Dict[str, Any] = {
            "inputs": prompt,
            "parameters": {
                "temperature": self.config.temperature,
                "max_new_tokens": self.config.max_output_tokens,
                "return_full_text": False,
            },
        }
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
        except Exception as exc:
            LOGGER.error("LLM request failed (huggingface): %s", exc)
            return None

        data = response.json()
        if isinstance(data, list) and data:
            generated = data[0].get("generated_text") if isinstance(data[0], dict) else None
            if isinstance(generated, str):
                return generated.strip()
        if isinstance(data, dict):
            generated = data.get("generated_text") or data.get("text")
            if isinstance(generated, str):
                return generated.strip()
        LOGGER.error("Unexpected Hugging Face response format: %s", data)
        return None

    def _parse_structured_response(self, raw_text: str, context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        try:
            payload = json.loads(raw_text)
            recommended = payload.get("recommended_action", {})
            response = LLMResponse(
                risk_summary=str(payload["risk_summary"]),
                likely_root_cause=str(payload["likely_root_cause"]),
                confidence=float(payload["confidence"]),
                recommended_action=LLMRecommendedAction(
                    type=str(recommended["type"]),
                    parameters={
                        str(key): str(value)
                        for key, value in recommended.get("parameters", {}).items()
                    },
                ),
            )
            return AgentOutput(response=response, raw_text=raw_text)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Failed to parse LLM response as structured payload: %s", exc)
            fallback_context = dict(context or {})
            fallback_context.update({"raw_text": raw_text, "parse_error": str(exc)})
            return self.fallback.generate_action_plan(fallback_context)

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        pipeline = context.get("pipeline_id", "unknown pipeline")
        risk = context.get("predicted_risk")
        risk_text = f"{risk:.2f}" if isinstance(risk, (int, float)) else "n/a"
        failed_tasks = context.get("failed_tasks") or []
        latest_error = context.get("latest_error") or "Not captured"
        telemetry_summary = context.get("telemetry_summary") or []

        summary_block = "\n".join(f"* {item}" for item in telemetry_summary[:8])

        schema_hint = json.dumps(
            {
                "risk_summary": "<string>",
                "likely_root_cause": "<string>",
                "confidence": 0.85,
                "recommended_action": {
                    "type": "retry|tune|skip|alert|none",
                    "parameters": {"key": "value"},
                },
            },
            ensure_ascii=False,
        )

        return (
            f"Pipeline: {pipeline}\n"
            f"Predicted Failure Risk: {risk_text}\n"
            f"Failed Tasks: {', '.join(failed_tasks) if failed_tasks else 'None'}\n"
            f"Latest Error: {latest_error}\n"
            f"Telemetry Highlights:\n{summary_block if summary_block else 'None recorded.'}\n"
            "Respond with a single JSON object following this template. Confidence must be 0..1."
            f"\nSchema Example: {schema_hint}"
        )

    @staticmethod
    def _unwrap_output(response: Any) -> Optional[str]:  # pragma: no cover - provider specific
        # Attempt to navigate common OpenAI response formats without hard dependency.
        if hasattr(response, "output"):
            output = getattr(response, "output")
            if isinstance(output, list) and output:
                content = output[0].get("content") if isinstance(output[0], dict) else None
                if isinstance(content, list) and content:
                    text = content[0].get("text")
                    if isinstance(text, str):
                        return text
        if hasattr(response, "choices"):
            choices = getattr(response, "choices")
            if choices and hasattr(choices[0], "message"):
                message = choices[0].message
                if isinstance(message, dict) and "content" in message:
                    return str(message["content"])
        return None
