"""Interpreter for the FusionFlow temporal specification language"""

from typing import Any

from .ast_nodes import (
    Program,
    DatasetDeclaration,
    PipelineDefinition,
    ModelDefinition,
    ExperimentDefinition,
    TimelineDefinition,
    MergeStatement,
    Literal,
    Identifier,
)
from .runtime import Runtime


class Interpreter:
    def __init__(self, runtime: Runtime | None = None):
        self.runtime = runtime or Runtime()

    def execute(self, ast):
        if isinstance(ast, Program):
            for statement in ast.statements:
                self.execute_statement(statement)
        else:
            self.execute_statement(ast)

    def execute_statement(self, stmt):
        if isinstance(stmt, DatasetDeclaration):
            self.runtime.register_dataset(stmt)
        elif isinstance(stmt, PipelineDefinition):
            self.runtime.register_pipeline(stmt)
        elif isinstance(stmt, ModelDefinition):
            resolved_model = self.resolve_model_definition(stmt)
            self.runtime.register_model(resolved_model)
        elif isinstance(stmt, ExperimentDefinition):
            self.runtime.register_experiment(self.runtime.current_timeline, stmt)
        elif isinstance(stmt, TimelineDefinition):
            self.execute_timeline_definition(stmt)
        elif isinstance(stmt, MergeStatement):
            self.runtime.record_merge(stmt)

    def execute_timeline_definition(self, stmt: TimelineDefinition):
        previous_timeline = self.runtime.current_timeline
        self.runtime.create_timeline(stmt.name, stmt.description, parent=previous_timeline)
        self.runtime.current_timeline = stmt.name

        try:
            for experiment in stmt.experiments:
                self.execute_statement(experiment)
        finally:
            self.runtime.current_timeline = previous_timeline

    def materialize_literal(self, value) -> Any:
        if isinstance(value, Literal):
            return value.value
        if isinstance(value, Identifier):
            return value.name
        return value

    def resolve_model_definition(self, stmt: ModelDefinition) -> ModelDefinition:
        resolved_params = {key: self.materialize_literal(value) for key, value in stmt.params.items()}
        return ModelDefinition(name=stmt.name, type_name=stmt.type_name, params=resolved_params)
