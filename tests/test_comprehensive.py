import pytest

from fusionflow.interpreter import Interpreter
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.runtime import Runtime


def interpret(source: str) -> Runtime:
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(ast)
    return runtime


def test_duplicate_dataset_version_not_allowed():
    source = """
    dataset customers v1
        source "customers_v1.csv"
    end

    dataset customers v1
        source "customers_v1_reimport.csv"
    end
    """

    with pytest.raises(ValueError):
        interpret(source)


def test_pipeline_requires_declared_dataset():
    source = """
    pipeline churn_features
        from customers v1
    end
    """

    with pytest.raises(ValueError):
        interpret(source)


def test_timeline_parent_tracking():
    source = """
    dataset customers v1
        source "customers.csv"
    end

    pipeline baseline
        from customers v1
    end

    model rf_v1
        type random_forest
    end

    timeline v2 "Branch"
        experiment churn_test
            uses pipeline baseline
            uses model rf_v1
            metrics [accuracy]
        end
    end
    """

    runtime = interpret(source)

    assert runtime.timelines['v2'].parent == 'main'
    assert runtime.current_timeline == 'main'


def test_model_params_materialized():
    source = """
    model rf_v1
        type random_forest
        params { trees: 200, mode: fast }
    end
    """

    runtime = interpret(source)
    model = runtime.models['rf_v1']
    assert model.params['trees'] == 200
    assert model.params['mode'] == 'fast'


def test_merge_requires_known_timelines():
    source = """
    merge v2 into main
        because "Missing timeline"
        strategy prefer_metrics f1
    end
    """

    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    runtime = Runtime()
    interpreter = Interpreter(runtime)

    with pytest.raises(ValueError):
        interpreter.execute(ast)
