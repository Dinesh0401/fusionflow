"""Load IR JSON dicts into typed ExecutionPlan dataclasses.

The IR format is the contract between frontends and backends.
v0.4 IR has explicit `ir_version` field; v0.3 IR doesn't (defaults to "0.3").
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from fusionflow.executor.plan import (
    CheckpointOp,
    DatasetSpec,
    DeriveOp,
    ExecutionPlan,
    FeaturesOp,
    ModelSpec,
    Op,
    PipelineSpec,
    SelectOp,
    SplitOp,
    TargetOp,
    WhereOp,
)


SUPPORTED_IR_VERSIONS = frozenset({"0.3", "0.4"})
V04_ONLY_OPS = frozenset({"where", "split", "features", "checkpoint"})


class IRLoadError(ValueError):
    """Raised when IR cannot be loaded into an ExecutionPlan."""


def _load_op(op_dict: Dict[str, Any]) -> Op:
    op_type = op_dict.get("type")
    if op_type == "derive":
        return DeriveOp(target=op_dict["target"], expression=op_dict["expression"])
    if op_type == "select":
        return SelectOp(fields=tuple(op_dict["fields"]))
    if op_type == "target":
        return TargetOp(field=op_dict["field"])
    if op_type == "where":
        return WhereOp(condition=op_dict["condition"])
    if op_type == "split":
        return SplitOp(train_ratio=float(op_dict["train_ratio"]))
    if op_type == "features":
        return FeaturesOp(fields=tuple(op_dict["fields"]))
    if op_type == "checkpoint":
        return CheckpointOp(name=op_dict["name"])
    raise IRLoadError(
        f"Unknown IR operation type: {op_type!r}. "
        f"Add a handler in fusionflow/executor/ir_loader.py::_load_op "
        f"and bump SUPPORTED_IR_VERSIONS if the IR shape changes."
    )


def _load_datasets(ir: Dict[str, Any]) -> Tuple[DatasetSpec, ...]:
    specs: List[DatasetSpec] = []
    for qualified_name, payload in ir.get("datasets", {}).items():
        specs.append(
            DatasetSpec(
                name=payload["name"],
                version=payload["version"],
                source=payload["source"],
                schema=dict(payload.get("schema", {})),
                description=payload.get("description"),
            )
        )
    return tuple(specs)


def _load_pipeline(ir: Dict[str, Any], pipeline_name: str) -> PipelineSpec:
    pipelines = ir.get("pipelines", {})
    if pipeline_name not in pipelines:
        raise IRLoadError(f"Pipeline {pipeline_name!r} not found in IR")
    payload = pipelines[pipeline_name]
    ops = tuple(_load_op(op) for op in payload.get("operations", []))
    return PipelineSpec(
        name=payload["name"],
        input_dataset=payload["input"],
        ops=ops,
    )


def _load_model(ir: Dict[str, Any], model_name: str) -> ModelSpec:
    models = ir.get("models", {})
    if model_name not in models:
        raise IRLoadError(f"Model {model_name!r} not found in IR")
    payload = models[model_name]
    return ModelSpec(
        name=model_name,
        type_name=payload["type"],
        params=dict(payload.get("params", {})),
    )


def _find_experiment(ir: Dict[str, Any], experiment_name: str) -> Tuple[str, Dict[str, Any]]:
    """Locate experiment by name across main + sub-timelines. Returns (timeline_name, payload)."""
    main_experiments = ir.get("experiments", {})
    if experiment_name in main_experiments:
        return ("main", main_experiments[experiment_name])
    for tl_name, tl_payload in ir.get("timelines", {}).items():
        tl_experiments = tl_payload.get("experiments", {})
        if experiment_name in tl_experiments:
            return (tl_name, tl_experiments[experiment_name])
    raise IRLoadError(f"Experiment {experiment_name!r} not found in IR")


def load_plan(ir: Dict[str, Any], experiment_name: str) -> ExecutionPlan:
    """Build an ExecutionPlan for one experiment from a v0.4 (or v0.3) IR dict."""
    ir_version = ir.get("ir_version", "0.3")
    if ir_version not in SUPPORTED_IR_VERSIONS:
        raise IRLoadError(
            f"Unsupported IR version: {ir_version!r}. "
            f"Supported: {sorted(SUPPORTED_IR_VERSIONS)}"
        )

    timeline, exp_payload = _find_experiment(ir, experiment_name)

    # Defensive check: v0.3 IR must not contain v0.4-only ops (e.g., from hand-editing)
    if ir_version == "0.3":
        all_ops_iter = list(ir.get("pipelines", {}).values())
        for tl in ir.get("timelines", {}).values():
            for exp in tl.get("experiments", {}).values():
                if exp.get("extension"):
                    all_ops_iter.append({"operations": exp["extension"]})
        for ops_holder in all_ops_iter:
            for op in ops_holder.get("operations", []):
                if op.get("type") in V04_ONLY_OPS:
                    raise IRLoadError(
                        f"IR version 0.3 contains v0.4-only operation type "
                        f"{op.get('type')!r}. Bump ir_version to '0.4' to use this op."
                    )

    pipeline = _load_pipeline(ir, exp_payload["pipeline"])
    model = _load_model(ir, exp_payload["model"])
    datasets = _load_datasets(ir)
    metrics = tuple(exp_payload.get("metrics", []))
    extension_ops = tuple(_load_op(op) for op in exp_payload.get("extension", []) or [])

    return ExecutionPlan(
        ir_version=ir_version,
        experiment_name=experiment_name,
        timeline=timeline,
        datasets=datasets,
        pipeline=pipeline,
        model=model,
        metrics=metrics,
        extension_ops=extension_ops,
    )
