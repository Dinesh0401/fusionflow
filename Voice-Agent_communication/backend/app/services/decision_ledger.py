import json
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models import DecisionRecord
from ..schemas.decision import DecisionGatePayload
from ..schemas.llm import LLMDecision


class DecisionLedger:
    """Append-only ledger for AI decision events."""

    SCHEMA_VERSION = "v1"

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._session_maker = sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def record_event(
        self,
        gate_result: DecisionGatePayload,
        llm_decision: LLMDecision | None,
        *,
        automation_executed: bool | None = None,
        downstream_failure: bool | None = None,
    ) -> DecisionRecord:
        """Persist a decision event to the ledger."""
        
        # Fallback values if LLM decision is missing (e.g. schema invalid or blocked before LLM)
        provider = llm_decision.provider if llm_decision else (gate_result.provider or "unknown")
        model = llm_decision.model if llm_decision else (gate_result.model or "unknown")
        prompt_hash = (
            llm_decision.prompt_hash
            if llm_decision
            else (gate_result.prompt_hash or "n/a")
        )
        action_type = (
            llm_decision.recommended_action.type.value
            if llm_decision and llm_decision.recommended_action
            else gate_result.decision_type
        )
        
        action_params = None
        if llm_decision and llm_decision.recommended_action.parameters:
            try:
                action_params = json.dumps(llm_decision.recommended_action.parameters)
            except (TypeError, ValueError):
                action_params = "{}"

        record = DecisionRecord(
            provider=provider,
            model=model,
            prompt_hash=prompt_hash,
            ml_risk_score=gate_result.ml_risk_score,
            llm_confidence=gate_result.llm_confidence,
            gate_verdict=gate_result.verdict.value,
            gate_reason=gate_result.reason,
            action_type=action_type,
            action_params=action_params,
            schema_valid=gate_result.schema_valid,
            schema_version=self.SCHEMA_VERSION,
            automation_executed=automation_executed,
            downstream_failure=downstream_failure,
        )

        async with self._session_maker() as session:
            session.add(record)
            await session.commit()
            await session.refresh(record)

        return record

    async def init_db(self) -> None:
        """Initialize the database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def backfill_prompt_hash(self, *, fallback_value: str = "legacy") -> int:
        """Assign a fallback hash to historical records lacking prompt identity."""

        async with self._session_maker() as session:
            result = await session.exec(
                select(DecisionRecord).where(
                    (DecisionRecord.prompt_hash == "n/a") | (DecisionRecord.prompt_hash == "")
                )
            )
            records = result.all()
            for record in records:
                record.prompt_hash = fallback_value
                session.add(record)
            if records:
                await session.commit()
            return len(records)
