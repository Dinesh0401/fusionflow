"""Token definitions for FusionFlow lexer"""

from enum import Enum, auto

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    
    # Keywords
    DATASET = auto()
    FROM = auto()
    PIPELINE = auto()
    END = auto()
    WHERE = auto()
    JOIN = auto()
    ON = auto()
    DERIVE = auto()
    FEATURES = auto()
    TARGET = auto()
    SPLIT = auto()
    EXPERIMENT = auto()
    MODEL = auto()
    USING = auto()
    METRICS = auto()
    PRINT = auto()
    OF = auto()
    CHECKPOINT = auto()
    TIMELINE = auto()
    MERGE = auto()
    INTO = auto()
    UNDO = auto()
    VERSIONED = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    EQUALS = auto()
    DOUBLE_EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()
    PERCENT = auto()
    
    # Special
    NEWLINE = auto()
    EOF = auto()

class Token:
    def __init__(self, type: TokenType, value, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}, {self.column})"
