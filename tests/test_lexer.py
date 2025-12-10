import pytest
from fusionflow.lexer import Lexer
from fusionflow.tokens import TokenType

def test_tokenize_simple():
    source = "dataset customers from \"data.csv\""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.DATASET
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[2].type == TokenType.FROM
    assert tokens[3].type == TokenType.STRING

def test_tokenize_pipeline():
    source = """
    pipeline test:
        from customers
        where age > 18
    end
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    token_types = [t.type for t in tokens if t.type != TokenType.NEWLINE]
    assert TokenType.PIPELINE in token_types
    assert TokenType.WHERE in token_types
    assert TokenType.END in token_types

def test_tokenize_operators():
    source = "x == 5 and y != 10"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert any(t.type == TokenType.DOUBLE_EQUALS for t in tokens)
    assert any(t.type == TokenType.AND for t in tokens)
    assert any(t.type == TokenType.NOT_EQUALS for t in tokens)

def test_tokenize_numbers():
    source = "123 45.67"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == 123
    assert tokens[1].type == TokenType.NUMBER
    assert tokens[1].value == 45.67

def test_tokenize_strings():
    source = '"hello" \'world\''
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello"
    assert tokens[1].type == TokenType.STRING
    assert tokens[1].value == "world"

def test_tokenize_comments():
    source = """
    dataset test from "file.csv"  # This is a comment
    # Another comment
    pipeline p:
    end
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Comments should be skipped
    assert all(t.type != TokenType.IDENTIFIER or t.value != "#" for t in tokens)

def test_tokenize_comparison():
    source = "a < b and c >= d or e <= f"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    token_types = [t.type for t in tokens]
    assert TokenType.LESS_THAN in token_types
    assert TokenType.GREATER_EQUAL in token_types
    assert TokenType.LESS_EQUAL in token_types

def test_tokenize_delimiters():
    source = "features [a, b, c]"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert any(t.type == TokenType.LBRACKET for t in tokens)
    assert any(t.type == TokenType.RBRACKET for t in tokens)
    assert any(t.type == TokenType.COMMA for t in tokens)

def test_tokenize_member_access():
    source = "customers.age"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[1].type == TokenType.DOT
    assert tokens[2].type == TokenType.IDENTIFIER
