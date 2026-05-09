"""Typed dataclasses for FusionFlow execution plans.

A plan represents one experiment's complete execution path: load datasets,
apply pipeline ops (with optional extension overrides), train the model,
evaluate metrics. Plans are immutable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DatasetSpec:
    """Dataset reference: name, version, source path, and schema."""
    name: str
    version: str
    source: str
    schema: Dict[str, str]
    description: Optional[str] = None

    @property
    def qualified_name(self) -> str:
        return f"{self.name}:{self.version}"


@dataclass(frozen=True)
class Op:
    """Base class for all execution operations. Subclasses define semantics."""


@dataclass(frozen=True)
class DeriveOp(Op):
    target: str
    expression: str  # IR carries expressions as strings (consistent with v0.4 IR)


@dataclass(frozen=True)
class SelectOp(Op):
    fields: Tuple[str, ...]


@dataclass(frozen=True)
class TargetOp(Op):
    field: str


@dataclass(frozen=True)
class WhereOp(Op):
    condition: str


@dataclass(frozen=True)
class SplitOp(Op):
    train_ratio: float


@dataclass(frozen=True)
class FeaturesOp(Op):
    fields: Tuple[str, ...]


@dataclass(frozen=True)
class CheckpointOp(Op):
    name: str


@dataclass(frozen=True)
class TrainOp(Op):
    """Auto-injected by the loader from experiment.model. Tells the backend
    'fit the model now using current train split as input.'"""
    model: str  # model name; resolved against ExecutionPlan.model


@dataclass(frozen=True)
class EvalOp(Op):
    """Auto-injected by the loader from experiment.metrics."""
    metrics: Tuple[str, ...]


@dataclass(frozen=True)
class PipelineSpec:
    """Ordered ops to apply to a loaded dataset."""
    name: str
    input_dataset: str  # qualified name "name:version"
    ops: Tuple[Op, ...]


@dataclass(frozen=True)
class ModelSpec:
    """Model declaration: type and params."""
    name: str
    type_name: str
    params: Dict[str, Any]


@dataclass(frozen=True)
class ExecutionPlan:
    """One experiment's complete execution path.

    Plans are immutable. Backends consume them via ``ExecutionBackend.execute``.
    Use ``all_ops`` to get the canonical execution sequence (pipeline ops ->
    extension overrides -> TrainOp -> EvalOp).
    """
    ir_version: str
    experiment_name: str
    timeline: str  # "main" if not in a sub-timeline
    datasets: Tuple[DatasetSpec, ...]
    pipeline: PipelineSpec
    model: ModelSpec
    metrics: Tuple[str, ...]
    extension_ops: Tuple[Op, ...] = field(default_factory=tuple)

    @property
    def all_ops(self) -> Tuple[Op, ...]:
        """Effective op sequence: pipeline.ops + extension_ops + TrainOp + EvalOp.

        This is the canonical order the backend should execute. Backends needing
        a non-linear lifecycle (e.g. interleaved train/eval for streaming) should
        read pipeline.ops, extension_ops, model, and metrics directly rather than
        relying on this property.
        """
        return (
            *self.pipeline.ops,
            *self.extension_ops,
            TrainOp(self.model.name),
            EvalOp(self.metrics),
        )
