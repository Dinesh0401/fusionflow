"""Backend Protocol for FusionFlow execution.

A backend takes an ExecutionPlan and produces a RunResult. Different backends
(Pandas, Spark, Polars, ...) plug in here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Protocol, runtime_checkable

from fusionflow.executor.plan import ExecutionPlan
from fusionflow.executor.run_result import RunResult


@dataclass
class SupportReport:
    """A backend's verdict on whether it can execute a given plan."""
    supported: bool
    unsupported_ops: List[str] = field(default_factory=list)
    reason: str = ""


@runtime_checkable
class ExecutionBackend(Protocol):
    """Backend protocol. Contract:

    - ``name`` is a unique short string identifier (e.g., "pandas", "spark").
    - ``supports(plan)`` is consulted first; backends MUST NOT raise on
      unsupported plans -- return ``SupportReport(supported=False, ...)`` instead.
    - ``execute(plan)`` MUST return a ``RunResult`` with ``status=FAILED`` rather
      than raising for plan-level errors. Reserve raises for genuine bugs.

    Note: ``@runtime_checkable`` only verifies attribute presence, not signatures.
    Add explicit contract tests when introducing a new backend.
    """

    name: str

    def supports(self, plan: ExecutionPlan) -> SupportReport: ...

    def execute(self, plan: ExecutionPlan) -> RunResult: ...
