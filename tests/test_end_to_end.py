import pytest
import pandas as pd
import numpy as np
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.interpreter import Interpreter
from fusionflow.runtime import Runtime
import tempfile
import os

@pytest.fixture
def sample_data():
    """Create sample CSV data for testing"""
    data = pd.DataFrame({
        'age': [25, 35, 45, 55, 65],
        'income': [30000, 50000, 70000, 90000, 110000],
        'churned': [0, 0, 1, 1, 0]
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        yield f.name
    
    os.unlink(f.name)

def test_end_to_end_simple(sample_data):
    """Test simple dataset loading"""
    source = f'dataset customers from "{sample_data}"'
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    runtime = Runtime()
    interpreter = Interpreter(runtime)
    interpreter.execute(ast)
    
    assert 'customers' in runtime.datasets
    assert len(runtime.datasets['customers']) == 5

def test_end_to_end_pipeline(sample_data):
    """Test pipeline execution"""
    source = f"""
    dataset customers from "{sample_data}"
    
    pipeline churn_pipeline:
        from customers
        where age > 30
        derive age_bracket = age / 10
        features [age, income]
        target churned
        split 80% train, 20% test
    end
    """
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    runtime = Runtime()
    interpreter = Interpreter(runtime)
    interpreter.execute(ast)
    
    assert 'churn_pipeline' in runtime.pipelines
    pipeline_data = runtime.get_state().get('pipeline_churn_pipeline')
    assert pipeline_data is not None
    assert len(pipeline_data['data']) == 4  # 4 records with age > 30

def test_end_to_end_experiment(sample_data):
    """Test full ML experiment"""
    source = f"""
    dataset customers from "{sample_data}"
    
    pipeline churn_pipeline:
        from customers
        features [age, income]
        target churned
        split 80% train, 20% test
    end
    
    experiment churn_exp:
        model random_forest
        using churn_pipeline
        metrics [accuracy, f1]
    end
    """
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    runtime = Runtime()
    interpreter = Interpreter(runtime)
    interpreter.execute(ast)
    
    assert 'churn_exp' in runtime.experiments
    exp = runtime.get_experiment('churn_exp')
    assert 'accuracy' in exp['metrics']
    assert exp['metrics']['accuracy'] is not None
