import pytest
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.ast_nodes import *

def test_parse_dataset():
    source = 'dataset customers from "data.csv"'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], DatasetDeclaration)
    assert ast.statements[0].name == "customers"
    assert ast.statements[0].path == "data.csv"

def test_parse_pipeline():
    source = """
    pipeline test:
        from customers
        where age > 18
        features [age, income]
        target churned
        split 80% train, 20% test
    end
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert len(ast.statements) == 1
    pipeline = ast.statements[0]
    assert isinstance(pipeline, PipelineDefinition)
    assert pipeline.name == "test"
    assert len(pipeline.body) > 0

def test_parse_experiment():
    source = """
    experiment exp1:
        model random_forest
        using pipeline1
        metrics [accuracy, f1]
    end
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert len(ast.statements) == 1
    exp = ast.statements[0]
    assert isinstance(exp, ExperimentDefinition)
    assert exp.model_type == "random_forest"
    assert "accuracy" in exp.metrics

def test_parse_expression():
    source = """
    pipeline test:
        from data
        derive total = price * quantity
    end
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    pipeline = ast.statements[0]
    derive_clause = pipeline.body[1]
    assert isinstance(derive_clause, DeriveClause)
    assert isinstance(derive_clause.expression, BinaryOp)

def test_parse_checkpoint():
    source = 'checkpoint "baseline"'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert isinstance(ast.statements[0], CheckpointStatement)
    assert ast.statements[0].name == "baseline"

def test_parse_timeline():
    source = """
    timeline "exp1" {
        dataset test from "test.csv"
    }
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert isinstance(ast.statements[0], TimelineStatement)
    assert ast.statements[0].name == "exp1"

def test_parse_print():
    source = 'print metrics of experiment1'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert isinstance(ast.statements[0], PrintStatement)
    assert ast.statements[0].what == "metrics"

def test_parse_merge():
    source = 'merge "exp1" into "main"'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert isinstance(ast.statements[0], MergeStatement)
    assert ast.statements[0].source_timeline == "exp1"
