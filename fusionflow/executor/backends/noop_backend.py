"""NoopBackend: validates plan structure and returns a SKIPPED RunResult.

Used for tests, --dry-run mode, and plan inspection. Never reads data, never
trains models. Returns SUCCESS only when supports() agrees, SKIPPED otherwise."""

from __future__ import annotations

from typing import List

from fusionflow.executor.plan import (
    CheckpointOp,
    DeriveOp,
    EvalOp,
    ExecutionPlan,
    FeaturesOp,
    Op,
    SelectOp,
    SplitOp,
    TargetOp,
    TrainOp,
    WhereOp,
)
from fusionflow.executor.run_result import RunResult, RunStatus
from fusionflow.executor.backends import SupportReport


_KNOWN_OP_TYPES = (
    DeriveOp,
    SelectOp,
    TargetOp,
    WhereOp,
    SplitOp,
    FeaturesOp,
    CheckpointOp,
    TrainOp,
    EvalOp,
)


class NoopBackend:
    name = "noop"

    def supports(self, plan: ExecutionPlan) -> SupportReport:
        unsupported: List[str] = []
        for op in plan.all_ops:
            if not isinstance(op, _KNOWN_OP_TYPES):
                unsupported.append(type(op).__name__)
        if unsupported:
            return SupportReport(
                supported=False,
                unsupported_ops=unsupported,
                reason=f"NoopBackend cannot identify op types: {sorted(set(unsupported))}",
            )
        return SupportReport(supported=True)

    def execute(self, plan: ExecutionPlan) -> RunResult:
        report = self.supports(plan)
        if not report.supported:
            return RunResult(
                experiment=plan.experiment_name,
                backend=self.name,
                status=RunStatus.FAILED,
                ir_version=plan.ir_version,
                detail=report.reason,
            )
        return RunResult(
            experiment=plan.experiment_name,
            backend=self.name,
            status=RunStatus.SKIPPED,
            ir_version=plan.ir_version,
            detail=f"NoopBackend skipped {len(plan.all_ops)} operations.",
        )
