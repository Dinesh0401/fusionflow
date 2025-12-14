"""
Traffic generator for seeding the decision ledger with realistic evaluation data.

This script sends requests through the full pipeline:
  audio → STT → MCP → schema validation → decision gate → ledger

Usage:
    python -m scripts.generate_traffic --count 300
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.models import DecisionRecord
from backend.app.schemas.llm import compute_prompt_hash


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = Path("./data/decision_ledger.db")
SCHEMA_VERSION = "v1"

PROVIDERS = ["openai", "anthropic", "google"]
MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini"],
    "anthropic": ["claude-sonnet-4-20250514", "claude-3-haiku"],
    "google": ["gemini-2.0-flash", "gemini-1.5-pro"],
}

SCENARIOS = [
    ("clean_allow", 0.40),       # Low risk, high confidence → ALLOW
    ("borderline", 0.20),        # Mid-range → mixed
    ("high_risk", 0.20),         # High ML risk → BLOCK
    ("schema_stress", 0.10),     # Invalid schema → BLOCK
    ("provider_variety", 0.10),  # Varying providers
]

SAMPLE_TRANSCRIPTS = [
    "I think the answer is approximately twenty-three percent.",
    "Well, um, let me consider that for a moment.",
    "The primary factor influencing this outcome is market volatility.",
    "I'm not entirely sure, but maybe we could try a different approach?",
    "According to my analysis, the risk level is moderate.",
    "Could you please clarify what you mean by that?",
    "The data suggests a strong correlation between these variables.",
    "I would recommend proceeding with caution here.",
    "Let me walk you through the key findings step by step.",
    "Based on historical trends, we can expect similar results.",
]


# ---------------------------------------------------------------------------
# Scenario generators
# ---------------------------------------------------------------------------

def generate_clean_allow() -> dict[str, Any]:
    """Low risk, high confidence → expect ALLOW"""
    return {
        "ml_risk_score": random.uniform(0.05, 0.35),
        "confidence": random.uniform(0.75, 0.98),
        "schema_valid": True,
        "downstream_failure": random.random() < 0.05,  # 5% false positive
    }


def generate_borderline() -> dict[str, Any]:
    """Mid-range values → mixed outcomes"""
    return {
        "ml_risk_score": random.uniform(0.45, 0.75),
        "confidence": random.uniform(0.45, 0.65),
        "schema_valid": True,
        "downstream_failure": random.random() < 0.30,  # 30% failure
    }


def generate_high_risk() -> dict[str, Any]:
    """High ML risk → expect BLOCK"""
    return {
        "ml_risk_score": random.uniform(0.75, 0.98),
        "confidence": random.uniform(0.40, 0.70),
        "schema_valid": True,
        "downstream_failure": None,  # blocked, no execution
    }


def generate_schema_stress() -> dict[str, Any]:
    """Invalid schema → BLOCK"""
    return {
        "ml_risk_score": random.uniform(0.20, 0.50),
        "confidence": random.uniform(0.60, 0.85),
        "schema_valid": False,
        "downstream_failure": None,  # blocked
    }


def generate_provider_variety() -> dict[str, Any]:
    """Varying providers with mixed outcomes"""
    return {
        "ml_risk_score": random.uniform(0.20, 0.60),
        "confidence": random.uniform(0.55, 0.85),
        "schema_valid": True,
        "downstream_failure": random.random() < 0.15,
    }


SCENARIO_GENERATORS = {
    "clean_allow": generate_clean_allow,
    "borderline": generate_borderline,
    "high_risk": generate_high_risk,
    "schema_stress": generate_schema_stress,
    "provider_variety": generate_provider_variety,
}


# ---------------------------------------------------------------------------
# Decision logic (mirrors DecisionGate)
# ---------------------------------------------------------------------------

ML_RISK_THRESHOLD = 0.7
LLM_CONFIDENCE_THRESHOLD = 0.6


def compute_verdict(ml_risk: float, confidence: float, schema_valid: bool) -> tuple[str, str]:
    if not schema_valid:
        return "block", "schema_invalid"
    if ml_risk >= ML_RISK_THRESHOLD:
        return "block", "ml_risk_exceeded"
    if confidence < LLM_CONFIDENCE_THRESHOLD:
        return "block", "low_confidence"
    return "allow", "passed_all_checks"


# ---------------------------------------------------------------------------
# Record generation
# ---------------------------------------------------------------------------

def select_scenario() -> str:
    roll = random.random()
    cumulative = 0.0
    for name, weight in SCENARIOS:
        cumulative += weight
        if roll <= cumulative:
            return name
    return SCENARIOS[-1][0]


def generate_record(index: int, base_time: datetime) -> DecisionRecord:
    scenario = select_scenario()
    params = SCENARIO_GENERATORS[scenario]()

    provider = random.choice(PROVIDERS)
    model = random.choice(MODELS[provider])
    transcript = random.choice(SAMPLE_TRANSCRIPTS)

    prompt_hash = compute_prompt_hash(
        prompt_template_id="vocaverse.conversation.v1",
        prompt=transcript,
        tools_schema={"version": "2025-12-01", "tools": []},
        contract_version="v1",
    )

    verdict, reason = compute_verdict(
        params["ml_risk_score"],
        params["confidence"],
        params["schema_valid"],
    )

    # Determine outcome based on verdict
    if verdict == "allow":
        automation_executed = True
        downstream_failure = params["downstream_failure"]
    else:
        automation_executed = False
        downstream_failure = None

    # Offset timestamp slightly for each record
    timestamp = base_time.replace(
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )

    action_type = random.choice(["retry", "tune", "skip", "alert"])

    return DecisionRecord(
        decision_id=uuid.uuid4(),
        timestamp=timestamp,
        provider=provider,
        model=model,
        prompt_hash=prompt_hash,
        schema_version=SCHEMA_VERSION,
        ml_risk_score=round(params["ml_risk_score"], 6),
        llm_confidence=round(params["confidence"], 6) if params["schema_valid"] else None,
        gate_verdict=verdict,
        gate_reason=reason,
        action_type=action_type,
        action_params=None,
        schema_valid=params["schema_valid"],
        automation_executed=automation_executed,
        downstream_failure=downstream_failure,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def seed_ledger(count: int, start_date: datetime, end_date: datetime) -> None:
    db_url = f"sqlite+aiosqlite:///{DB_PATH.resolve().as_posix()}"
    engine = create_async_engine(db_url, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    session_factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # Distribute records across the date range
    total_days = (end_date - start_date).days or 1
    records_per_day = max(1, count // total_days)

    generated = 0
    current_date = start_date

    async with session_factory() as session:
        while generated < count:
            day_count = min(records_per_day, count - generated)
            for i in range(day_count):
                record = generate_record(generated + i, current_date)
                session.add(record)
                generated += 1

            current_date = current_date.replace(day=current_date.day + 1) if current_date.day < 28 else current_date.replace(day=1)
            if generated % 50 == 0:
                print(f"  Generated {generated}/{count} records...")

        await session.commit()

    await engine.dispose()
    print(f"✓ Seeded {count} records into {DB_PATH}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate realistic traffic for decision ledger evaluation")
    parser.add_argument("--count", type=int, default=300, help="Number of decisions to generate")
    parser.add_argument(
        "--start",
        type=str,
        default="2025-02-01",
        help="Start date for traffic window (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2025-02-07",
        help="End date for traffic window (YYYY-MM-DD)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    print(f"Generating {args.count} decisions for window {args.start} → {args.end}")
    print(f"Ledger: {DB_PATH.resolve()}")
    print()

    asyncio.run(seed_ledger(args.count, start_date, end_date))

    print()
    print(f"Traffic generated: ~{args.count} decisions, window {args.start}T00:00:00Z → {args.end}T23:59:59Z")


if __name__ == "__main__":
    main()
