"""FusionFlow executor: loads IR into ExecutionPlan and dispatches to backends.

The executor consumes IR only — never AST. This is the contract that lets
parser additions stay backwards-compatible.
"""

from fusionflow.executor.ir_loader import load_plan
from fusionflow.executor.metrics import (
    UnknownMetricError,
    compute_metric,
    supported_metrics,
)
from fusionflow.executor.models import (
    UnknownModelTypeError,
    build_model,
    supported_model_types,
)
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
from fusionflow.executor.run_context import RunContext
from fusionflow.executor.run_result import RunResult, RunStatus
from fusionflow.executor.backends import ExecutionBackend, SupportReport
from fusionflow.executor.backends.noop_backend import NoopBackend
from fusionflow.executor.backends.pandas_backend import (
    PandasBackend,
    PandasExecutionError,
)

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
    "RunContext",
    "RunResult",
    "RunStatus",
    "ExecutionBackend",
    "SupportReport",
    "NoopBackend",
    "PandasBackend",
    "PandasExecutionError",
    "build_model",
    "supported_model_types",
    "UnknownModelTypeError",
    "compute_metric",
    "supported_metrics",
    "UnknownMetricError",
]
