import pytest

from fusionflow.lexer import Lexer
from fusionflow.tokens import TokenType


def extract_token_types(source: str):
    return [token.type for token in Lexer(source).tokenize()]


def test_dataset_header_tokens():
    types = extract_token_types('dataset customers v1')
    assert types[0] == TokenType.DATASET
    assert types[1] == TokenType.IDENTIFIER
    assert types[2] == TokenType.IDENTIFIER


def test_pipeline_keywords():
    source = """
    pipeline churn_features
        from customers v1
        derive spend_per_day = amount / days
        select [amount, days]
        target churned
    end
    """
    token_types = [t for t in extract_token_types(source) if t != TokenType.NEWLINE]
    assert TokenType.PIPELINE in token_types
    assert TokenType.FROM in token_types
    assert TokenType.DERIVE in token_types
    assert TokenType.SELECT in token_types
    assert TokenType.TARGET in token_types
    assert TokenType.END in token_types


def test_model_tokens():
    source = """
    model rf_v1
        type random_forest
        params { trees: 200 }
    end
    """
    token_types = [t for t in extract_token_types(source) if t != TokenType.NEWLINE]
    assert TokenType.MODEL in token_types
    assert TokenType.TYPE in token_types
    assert TokenType.PARAMS in token_types
    assert TokenType.LBRACE in token_types
    assert TokenType.END in token_types


def test_timeline_and_merge_tokens():
    source = """
    timeline v2 "Feature exploration"
        experiment churn_interaction
            uses pipeline churn_features
            uses model rf_v1
            metrics [accuracy]
        end
    end

    merge v2 into main
        because "Metrics improved"
        strategy prefer_metrics f1
    end
    """
    token_types = [t for t in extract_token_types(source) if t != TokenType.NEWLINE]
    assert TokenType.TIMELINE in token_types
    assert TokenType.EXPERIMENT in token_types
    assert TokenType.USES in token_types
    assert TokenType.METRICS in token_types
    assert TokenType.MERGE in token_types
    assert TokenType.BECAUSE in token_types
    assert TokenType.STRATEGY in token_types


def test_expression_tokens():
    source = "derive score = (a + b) / 2"
    tokens = Lexer(source).tokenize()
    assert any(t.type == TokenType.LPAREN for t in tokens)
    assert any(t.type == TokenType.RPAREN for t in tokens)
    assert any(t.type == TokenType.PLUS for t in tokens)
    assert any(t.type == TokenType.DIVIDE for t in tokens)


def test_literal_tokenization():
    source = 'params { trees: 200, mode: "fast" }'
    tokens = Lexer(source).tokenize()
    number_tokens = [t for t in tokens if t.type == TokenType.NUMBER]
    string_tokens = [t for t in tokens if t.type == TokenType.STRING]
    assert number_tokens and number_tokens[0].value == 200
    assert string_tokens and string_tokens[0].value == "fast"
