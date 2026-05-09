"""FusionFlow executor: loads IR into ExecutionPlan and dispatches to backends.

The executor consumes IR only — never AST. This is the contract that lets
parser additions stay backwards-compatible.
"""

from fusionflow.executor.ir_loader import load_plan
from fusionflow.executor.plan import (
    ExecutionPlan,
    PipelineSpec,
    ModelSpec,
    DatasetSpec,
    Op,
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
from fusionflow.executor.run_result import RunResult, RunStatus
from fusionflow.executor.backends import ExecutionBackend, SupportReport
from fusionflow.executor.backends.noop_backend import NoopBackend

__all__ = [
    "load_plan",
    "ExecutionPlan",
    "PipelineSpec",
    "ModelSpec",
    "DatasetSpec",
    "Op",
    "DeriveOp",
    "SelectOp",
    "TargetOp",
    "WhereOp",
    "SplitOp",
    "FeaturesOp",
    "CheckpointOp",
    "TrainOp",
    "EvalOp",
    "RunResult",
    "RunStatus",
    "ExecutionBackend",
    "SupportReport",
    "NoopBackend",
]
