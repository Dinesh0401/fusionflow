"""Real Pandas execution backend.

Executes an ExecutionPlan against pandas + scikit-learn:

- Loads CSV/Parquet via pandas
- Applies derive/select/where/split via pandas operations
- Trains models from the model registry (``models.py``)
- Computes metrics via the metrics registry (``metrics.py``)
- Returns a structured ``RunResult``

All randomness is seeded via the constructor's ``seed`` parameter, so two runs
with the same seed produce byte-identical ``RunResult.to_json()`` output.

Path resolution: ``DatasetSpec.source`` is treated as a path relative to the
current working directory. Override by passing ``data_root`` to the constructor.

Convention for op order: ``split`` should be the last data-transformation op
before train/eval. Ops AFTER ``split`` (other than ``features``/``target``,
which only set context metadata) will not transform the resulting train/test
frames in v0.4. ``checkpoint`` is a no-op for v0.4 (logged for traceability).

If ``FeaturesOp`` is missing, the backend defaults to "all columns except
target". If ``SplitOp`` is missing, the entire dataset is used as both train
and test (bad ML practice but executable). If ``TargetOp`` is missing, the
backend fails the run with a clear error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from fusionflow.executor.backends import SupportReport
from fusionflow.executor.metrics import compute_metric, supported_metrics
from fusionflow.executor.models import build_model, supported_model_types
from fusionflow.executor.run_context import RunContext
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


@dataclass
class _ExecutionContext:
    """Mutable state during plan execution. Internal to PandasBackend."""

    df: Optional[pd.DataFrame] = None
    train_df: Optional[pd.DataFrame] = None
    test_df: Optional[pd.DataFrame] = None
    features: Optional[Tuple[str, ...]] = None
    target: Optional[str] = None
    model: Any = None
    checkpoints: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)


class PandasExecutionError(RuntimeError):
    """Raised internally when a plan cannot be executed.

    Caught by ``PandasBackend.execute`` and converted into a ``RunResult`` with
    ``status=FAILED`` -- backends MUST NOT propagate plan-level errors per the
    ``ExecutionBackend`` contract.
    """


class PandasBackend:
    """Executes ExecutionPlans on pandas + scikit-learn."""

    name = "pandas"

    def __init__(
        self,
        seed: int = 42,
        data_root: Optional[Path] = None,
        context: Optional["RunContext"] = None,
    ) -> None:
        if context is not None:
            context.apply_thread_pinning()
            self.seed = int(context.seed)
        else:
            self.seed = int(seed)
        self.data_root = Path(data_root) if data_root is not None else Path.cwd()

    def supports(self, plan: ExecutionPlan) -> SupportReport:
        unsupported: List[str] = []
        known_ops = (
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
        for op in plan.all_ops:
            if not isinstance(op, known_ops):
                unsupported.append(type(op).__name__)
        if plan.model.type_name not in supported_model_types():
            unsupported.append(f"model:{plan.model.type_name}")
        for metric_name in plan.metrics:
            if metric_name not in supported_metrics():
                unsupported.append(f"metric:{metric_name}")
        if unsupported:
            unique = sorted(set(unsupported))
            return SupportReport(
                supported=False,
                unsupported_ops=unique,
                reason=f"PandasBackend does not support: {unique}",
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

        ctx = _ExecutionContext()
        try:
            ctx.df = self._load_dataset(plan)
            for op in plan.all_ops:
                self._dispatch(op, ctx, plan)
        except PandasExecutionError as exc:
            return RunResult(
                experiment=plan.experiment_name,
                backend=self.name,
                status=RunStatus.FAILED,
                ir_version=plan.ir_version,
                detail=str(exc),
            )
        except (FileNotFoundError, KeyError, ValueError) as exc:
            # Plan-level errors: missing files, missing columns, bad params.
            # Per the ExecutionBackend contract, return FAILED rather than raising.
            return RunResult(
                experiment=plan.experiment_name,
                backend=self.name,
                status=RunStatus.FAILED,
                ir_version=plan.ir_version,
                detail=f"{type(exc).__name__}: {exc}",
            )

        return RunResult(
            experiment=plan.experiment_name,
            backend=self.name,
            status=RunStatus.SUCCESS,
            ir_version=plan.ir_version,
            metrics=dict(ctx.metrics),
            detail=f"Executed {len(plan.all_ops)} ops; checkpoints={ctx.checkpoints}",
        )

    # ---- helpers ----

    def _load_dataset(self, plan: ExecutionPlan) -> pd.DataFrame:
        target_qname = plan.pipeline.input_dataset
        for ds in plan.datasets:
            if ds.qualified_name == target_qname:
                source_path = self.data_root / ds.source
                if str(ds.source).endswith(".parquet"):
                    return pd.read_parquet(source_path)
                return pd.read_csv(source_path)
        raise PandasExecutionError(
            f"Dataset {target_qname!r} not found in plan.datasets"
        )

    def _dispatch(self, op: Op, ctx: _ExecutionContext, plan: ExecutionPlan) -> None:
        if isinstance(op, DeriveOp):
            self._apply_derive(op, ctx)
        elif isinstance(op, SelectOp):
            self._apply_select(op, ctx)
        elif isinstance(op, WhereOp):
            self._apply_where(op, ctx)
        elif isinstance(op, FeaturesOp):
            self._apply_features(op, ctx)
        elif isinstance(op, TargetOp):
            self._apply_target(op, ctx)
        elif isinstance(op, SplitOp):
            self._apply_split(op, ctx)
        elif isinstance(op, CheckpointOp):
            ctx.checkpoints.append(op.name)
        elif isinstance(op, TrainOp):
            self._apply_train(op, ctx, plan)
        elif isinstance(op, EvalOp):
            self._apply_eval(op, ctx)
        else:
            raise PandasExecutionError(
                f"PandasBackend cannot execute op type: {type(op).__name__}. "
                f"Add a branch in PandasBackend._dispatch."
            )

    def _apply_derive(self, op: DeriveOp, ctx: _ExecutionContext) -> None:
        assert ctx.df is not None
        df = ctx.df.copy()
        df[op.target] = df.eval(op.expression, engine="python")
        ctx.df = df

    def _apply_select(self, op: SelectOp, ctx: _ExecutionContext) -> None:
        assert ctx.df is not None
        ctx.df = ctx.df[list(op.fields)].copy()

    def _apply_where(self, op: WhereOp, ctx: _ExecutionContext) -> None:
        assert ctx.df is not None
        mask = ctx.df.eval(op.condition, engine="python")
        ctx.df = ctx.df[mask].copy()

    def _apply_features(self, op: FeaturesOp, ctx: _ExecutionContext) -> None:
        ctx.features = tuple(op.fields)

    def _apply_target(self, op: TargetOp, ctx: _ExecutionContext) -> None:
        ctx.target = op.field

    def _apply_split(self, op: SplitOp, ctx: _ExecutionContext) -> None:
        from sklearn.model_selection import train_test_split

        assert ctx.df is not None
        train, test = train_test_split(
            ctx.df,
            train_size=op.train_ratio,
            random_state=self.seed,
            shuffle=True,
        )
        ctx.train_df = train.reset_index(drop=True)
        ctx.test_df = test.reset_index(drop=True)

    def _apply_train(
        self, op: TrainOp, ctx: _ExecutionContext, plan: ExecutionPlan
    ) -> None:
        if ctx.target is None:
            raise PandasExecutionError(
                "Cannot train: no `target` op was declared in the pipeline."
            )
        # If no split, use the full df as both train and test.
        if ctx.train_df is None:
            assert ctx.df is not None
            ctx.train_df = ctx.df.copy()
            ctx.test_df = ctx.df.copy()
        # If no features, use all columns except target.
        if ctx.features is None:
            ctx.features = tuple(
                c for c in ctx.train_df.columns if c != ctx.target
            )
        X_train = ctx.train_df[list(ctx.features)]
        y_train = ctx.train_df[ctx.target]
        ctx.model = build_model(plan.model.type_name, plan.model.params, seed=self.seed)
        ctx.model.fit(X_train, y_train)

    def _apply_eval(self, op: EvalOp, ctx: _ExecutionContext) -> None:
        if (
            ctx.model is None
            or ctx.test_df is None
            or ctx.target is None
            or ctx.features is None
        ):
            raise PandasExecutionError(
                "Cannot evaluate: train was not run successfully."
            )
        X_test = ctx.test_df[list(ctx.features)]
        y_true = ctx.test_df[ctx.target]
        for metric_name in op.metrics:
            ctx.metrics[metric_name] = float(
                compute_metric(metric_name, ctx.model, X_test, y_true)
            )
