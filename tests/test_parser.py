import pytest

from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.ast_nodes import (
    Program,
    DatasetDeclaration,
    SchemaField,
    PipelineDefinition,
    DeriveStep,
    SelectStep,
    TargetStep,
    ModelDefinition,
    ExperimentDefinition,
    TimelineDefinition,
    MergeStatement,
    MergeStrategy,
    BinaryOp,
)


def parse_source(source: str) -> Program:
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def test_parse_dataset_with_schema():
    source = """
    dataset customers v1
        description "Customer base snapshot"
        source "s3://bucket/customers.csv"
        schema {
            id: int
            churned: bool
        }
    end
    """
    ast = parse_source(source)
    dataset = ast.statements[0]
    assert isinstance(dataset, DatasetDeclaration)
    assert dataset.name == "customers"
    assert dataset.version == "v1"
    assert dataset.source == "s3://bucket/customers.csv"
    assert dataset.description == "Customer base snapshot"
    assert dataset.schema == [SchemaField("id", "int"), SchemaField("churned", "bool")]


def test_parse_pipeline_definition():
    source = """
    pipeline churn_features
        from customers v1
        derive spend_per_day = amount / days
        select [spend_per_day, amount]
        target churned
    end
    """
    ast = parse_source(source)
    pipeline = ast.statements[0]
    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == "churn_features"
    assert pipeline.source.name == "customers"
    assert pipeline.source.version == "v1"
    assert isinstance(pipeline.steps[0], DeriveStep)
    assert isinstance(pipeline.steps[0].expression, BinaryOp)
    assert isinstance(pipeline.steps[1], SelectStep)
    assert isinstance(pipeline.steps[2], TargetStep)


def test_parse_model_with_params():
    source = """
    model rf_v1
        type random_forest
        params {
            trees: 200
            depth: 8
        }
    end
    """
    ast = parse_source(source)
    model = ast.statements[0]
    assert isinstance(model, ModelDefinition)
    assert model.type_name == "random_forest"
    assert set(model.params.keys()) == {"trees", "depth"}


def test_parse_experiment_with_extension():
    source = """
    experiment churn_baseline
        uses pipeline churn_features
        uses model rf_v1
        metrics [accuracy, f1]
        extend {
            derive bonus = spend_per_day * 0.1
        }
    end
    """
    ast = parse_source(source)
    exp = ast.statements[0]
    assert isinstance(exp, ExperimentDefinition)
    assert exp.pipeline == "churn_features"
    assert exp.model == "rf_v1"
    assert exp.metrics == ["accuracy", "f1"]
    assert exp.extension is not None
    assert isinstance(exp.extension.steps[0], DeriveStep)


def test_parse_timeline_with_nested_experiment():
    source = """
    timeline v2 "Feature exploration"
        experiment churn_interaction
            uses pipeline churn_features
            uses model rf_v1
            metrics [accuracy]
        end
    end
    """
    ast = parse_source(source)
    timeline = ast.statements[0]
    assert isinstance(timeline, TimelineDefinition)
    assert timeline.name == "v2"
    assert timeline.description == "Feature exploration"
    assert len(timeline.experiments) == 1
    assert timeline.experiments[0].name == "churn_interaction"


def test_parse_merge_statement():
    source = """
    merge v2 into main
        because "Improved f1 by 4%"
        strategy prefer_metrics f1
    end
    """
    ast = parse_source(source)
    merge_stmt = ast.statements[0]
    assert isinstance(merge_stmt, MergeStatement)
    assert merge_stmt.source_timeline == "v2"
    assert merge_stmt.target_timeline == "main"
    assert merge_stmt.justification == "Improved f1 by 4%"
    assert isinstance(merge_stmt.strategy, MergeStrategy)
    assert merge_stmt.strategy.name == "prefer_metrics"
    assert merge_stmt.strategy.arguments == ["f1"]
