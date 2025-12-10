"""Lexer for FusionFlow language"""

from .tokens import Token, TokenType

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        
        self.keywords = {
            'dataset': TokenType.DATASET,
            'from': TokenType.FROM,
            'pipeline': TokenType.PIPELINE,
            'end': TokenType.END,
            'where': TokenType.WHERE,
            'join': TokenType.JOIN,
            'on': TokenType.ON,
            'derive': TokenType.DERIVE,
            'features': TokenType.FEATURES,
            'target': TokenType.TARGET,
            'split': TokenType.SPLIT,
            'experiment': TokenType.EXPERIMENT,
            'model': TokenType.MODEL,
            'using': TokenType.USING,
            'metrics': TokenType.METRICS,
            'print': TokenType.PRINT,
            'of': TokenType.OF,
            'checkpoint': TokenType.CHECKPOINT,
            'timeline': TokenType.TIMELINE,
            'merge': TokenType.MERGE,
            'into': TokenType.INTO,
            'undo': TokenType.UNDO,
            'versioned': TokenType.VERSIONED,
            'and': TokenType.AND,
            'or': TokenType.OR,
            'not': TokenType.NOT,
            'true': TokenType.IDENTIFIER,
            'false': TokenType.IDENTIFIER,
        }
    
    def current_char(self):
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek_char(self, offset=1):
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self):
        if self.pos < len(self.source):
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def skip_whitespace(self):
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        if self.current_char() == '#':
            while self.current_char() and self.current_char() != '\n':
                self.advance()
    
    def read_number(self):
        start_col = self.column
        num_str = ''
        has_dot = False
        
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if has_dot:
                    break
                has_dot = True
            num_str += self.current_char()
            self.advance()
        
        value = float(num_str) if has_dot else int(num_str)
        return Token(TokenType.NUMBER, value, self.line, start_col)
    
    def read_string(self):
        start_col = self.column
        quote_char = self.current_char()
        self.advance()  # Skip opening quote
        
        string_value = ''
        while self.current_char() and self.current_char() != quote_char:
            if self.current_char() == '\\':
                self.advance()
                if self.current_char():
                    escape_chars = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', quote_char: quote_char}
                    string_value += escape_chars.get(self.current_char(), self.current_char())
                    self.advance()
            else:
                string_value += self.current_char()
                self.advance()
        
        if self.current_char() == quote_char:
            self.advance()  # Skip closing quote
        
        return Token(TokenType.STRING, string_value, self.line, start_col)
    
    def read_identifier(self):
        start_col = self.column
        identifier = ''
        
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            identifier += self.current_char()
            self.advance()
        
        token_type = self.keywords.get(identifier.lower(), TokenType.IDENTIFIER)
        return Token(token_type, identifier, self.line, start_col)
    
    def tokenize(self):
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            if not self.current_char():
                break
            
            if self.current_char() == '#':
                self.skip_comment()
                continue
            
            if self.current_char() == '\n':
                token = Token(TokenType.NEWLINE, '\n', self.line, self.column)
                self.tokens.append(token)
                self.advance()
                continue
            
            if self.current_char().isdigit():
                self.tokens.append(self.read_number())
                continue
            
            if self.current_char() in '"\'':
                self.tokens.append(self.read_string())
                continue
            
            if self.current_char().isalpha() or self.current_char() == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Operators and delimiters
            start_col = self.column
            char = self.current_char()
            
            if char == '+':
                self.tokens.append(Token(TokenType.PLUS, '+', self.line, start_col))
                self.advance()
            elif char == '-':
                self.tokens.append(Token(TokenType.MINUS, '-', self.line, start_col))
                self.advance()
            elif char == '*':
                self.tokens.append(Token(TokenType.MULTIPLY, '*', self.line, start_col))
                self.advance()
            elif char == '/':
                self.tokens.append(Token(TokenType.DIVIDE, '/', self.line, start_col))
                self.advance()
            elif char == '=':
                self.advance()
                if self.current_char() == '=':
                    self.tokens.append(Token(TokenType.DOUBLE_EQUALS, '==', self.line, start_col))
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.EQUALS, '=', self.line, start_col))
            elif char == '!':
                self.advance()
                if self.current_char() == '=':
                    self.tokens.append(Token(TokenType.NOT_EQUALS, '!=', self.line, start_col))
                    self.advance()
            elif char == '<':
                self.advance()
                if self.current_char() == '=':
                    self.tokens.append(Token(TokenType.LESS_EQUAL, '<=', self.line, start_col))
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.LESS_THAN, '<', self.line, start_col))
            elif char == '>':
                self.advance()
                if self.current_char() == '=':
                    self.tokens.append(Token(TokenType.GREATER_EQUAL, '>=', self.line, start_col))
                    self.advance()
                else:
                    self.tokens.append(Token(TokenType.GREATER_THAN, '>', self.line, start_col))
            elif char == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', self.line, start_col))
                self.advance()
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', self.line, start_col))
                self.advance()
            elif char == '[':
                self.tokens.append(Token(TokenType.LBRACKET, '[', self.line, start_col))
                self.advance()
            elif char == ']':
                self.tokens.append(Token(TokenType.RBRACKET, ']', self.line, start_col))
                self.advance()
            elif char == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', self.line, start_col))
                self.advance()
            elif char == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', self.line, start_col))
                self.advance()
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.line, start_col))
                self.advance()
            elif char == ':':
                self.tokens.append(Token(TokenType.COLON, ':', self.line, start_col))
                self.advance()
            elif char == '.':
                self.tokens.append(Token(TokenType.DOT, '.', self.line, start_col))
                self.advance()
            elif char == '%':
                self.tokens.append(Token(TokenType.PERCENT, '%', self.line, start_col))
                self.advance()
            else:
                raise SyntaxError(f"Unexpected character '{char}' at line {self.line}, column {self.column}")
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
