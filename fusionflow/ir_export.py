"""Temporal IR export utilities for FusionFlow specifications."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .ast_nodes import (
    BinaryOp,
    DatasetDeclaration,
    DeriveStep,
    ExperimentDefinition,
    Expression,
    Identifier,
    Literal,
    MemberAccess,
    MergeStatement,
    ModelDefinition,
    PipelineDefinition,
    PipelineExtension,
    PipelineStep,
    SchemaField,
    SelectStep,
    TargetStep,
    UnaryOp,
)
from .runtime import Runtime, TimelineSpec


_OPERATOR_PRECEDENCE: Dict[str, int] = {
    "or": 1,
    "and": 2,
    "==": 3,
    "!=": 3,
    "<": 4,
    "<=": 4,
    ">": 4,
    ">=": 4,
    "+": 5,
    "-": 5,
    "*": 6,
    "/": 6,
}


def _maybe_parenthesize(child: Expression, parent_op: str) -> str:
    child_text = _expression_to_string(child)
    if not isinstance(child, BinaryOp):
        return child_text

    parent_prec = _OPERATOR_PRECEDENCE.get(parent_op, 0)
    child_prec = _OPERATOR_PRECEDENCE.get(child.operator, 0)
    if child_prec < parent_prec:
        return f"({child_text})"
    return child_text


def _expression_to_string(expr: Expression) -> str:
    if isinstance(expr, Literal):
        if isinstance(expr.value, str):
            return json.dumps(expr.value)
        return str(expr.value)
    if isinstance(expr, Identifier):
        return expr.name
    if isinstance(expr, MemberAccess):
        return f"{_expression_to_string(expr.object)}.{expr.member}"
    if isinstance(expr, UnaryOp):
        operand = _expression_to_string(expr.operand)
        if expr.operator == "not":
            return f"not {operand}"
        return f"{expr.operator}{operand}"
    if isinstance(expr, BinaryOp):
        left = _maybe_parenthesize(expr.left, expr.operator)
        right = _maybe_parenthesize(expr.right, expr.operator)
        return f"{left} {expr.operator} {right}"

    raise TypeError(f"Unsupported expression node: {type(expr)}")


def _serialize_schema(schema: List[SchemaField]) -> Dict[str, str]:
    return {field.name: field.type_name for field in schema}


def _serialize_steps(steps: List[PipelineStep]) -> List[Dict[str, Any]]:
    operations: List[Dict[str, Any]] = []
    for step in steps:
        if isinstance(step, DeriveStep):
            operations.append(
                {
                    "type": "derive",
                    "target": step.variable,
                    "expression": _expression_to_string(step.expression),
                }
            )
        elif isinstance(step, SelectStep):
            operations.append({"type": "select", "fields": list(step.fields)})
        elif isinstance(step, TargetStep):
            operations.append({"type": "target", "field": step.field})
    return operations


def _serialize_dataset(dataset: DatasetDeclaration) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "name": dataset.name,
        "version": dataset.version,
        "source": dataset.source,
        "schema": _serialize_schema(dataset.schema),
    }
    if dataset.description:
        payload["description"] = dataset.description
    return payload


def _serialize_pipeline(pipeline: PipelineDefinition) -> Dict[str, Any]:
    return {
        "name": pipeline.name,
        "input": f"{pipeline.source.name}:{pipeline.source.version}",
        "operations": _serialize_steps(pipeline.steps),
    }


def _serialize_model(model: ModelDefinition) -> Dict[str, Any]:
    return {"type": model.type_name, "params": dict(model.params)}


def _serialize_extension(extension: Optional[PipelineExtension]) -> Optional[List[Dict[str, Any]]]:
    if not extension:
        return None
    operations = _serialize_steps(extension.steps)
    return operations or None


def _serialize_experiment(experiment: ExperimentDefinition) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "pipeline": experiment.pipeline,
        "model": experiment.model,
        "metrics": list(experiment.metrics),
    }
    if experiment.description:
        payload["description"] = experiment.description
    extension_ops = _serialize_extension(experiment.extension)
    if extension_ops:
        payload["extension"] = extension_ops
    return payload


def _serialize_timeline(name: str, timeline: TimelineSpec) -> Dict[str, Any]:
    experiments = {
        exp_name: _serialize_experiment(exp)
        for exp_name, exp in timeline.experiments.items()
    }
    payload: Dict[str, Any] = {
        "parent": timeline.parent,
        "experiments": experiments,
    }
    if timeline.description:
        payload["description"] = timeline.description
    return payload


def _serialize_merges(merges: List[MergeStatement]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for merge in merges:
        serialized.append(
            {
                "source": merge.source_timeline,
                "target": merge.target_timeline,
                "justification": merge.justification,
                "strategy": {
                    "name": merge.strategy.name,
                    "arguments": list(merge.strategy.arguments),
                },
            }
        )
    return serialized


def build_temporal_ir(runtime: Runtime) -> Dict[str, Any]:
    datasets = {
        f"{name}:{version}": _serialize_dataset(dataset)
        for (name, version), dataset in runtime.datasets.items()
    }

    pipelines = {
        name: _serialize_pipeline(pipeline)
        for name, pipeline in runtime.pipelines.items()
    }

    models = {
        name: _serialize_model(model)
        for name, model in runtime.models.items()
    }

    experiments: Dict[str, Any] = {}
    main_timeline = runtime.timelines.get("main")
    if main_timeline:
        experiments = {
            name: _serialize_experiment(experiment)
            for name, experiment in main_timeline.experiments.items()
        }

    timelines = {
        name: _serialize_timeline(name, timeline)
        for name, timeline in runtime.timelines.items()
        if name != "main"
    }

    merges = _serialize_merges(runtime.merges)

    return {
        "datasets": datasets,
        "pipelines": pipelines,
        "models": models,
        "experiments": experiments,
        "timelines": timelines,
        "merges": merges,
    }
