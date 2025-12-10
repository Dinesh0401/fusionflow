"""Parser for FusionFlow language"""

from .tokens import Token, TokenType
from .ast_nodes import *

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # Return EOF
    
    def peek_token(self, offset=1):
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]
    
    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
    
    def expect(self, token_type):
        token = self.current_token()
        if token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {token.type} at line {token.line}")
        self.advance()
        return token
    
    def skip_newlines(self):
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()
    
    def parse(self):
        statements = []
        self.skip_newlines()
        
        while self.current_token().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        return Program(statements)
    
    def parse_statement(self):
        token = self.current_token()
        
        if token.type == TokenType.DATASET:
            return self.parse_dataset_declaration()
        elif token.type == TokenType.PIPELINE:
            return self.parse_pipeline_definition()
        elif token.type == TokenType.EXPERIMENT:
            return self.parse_experiment_definition()
        elif token.type == TokenType.PRINT:
            return self.parse_print_statement()
        elif token.type == TokenType.CHECKPOINT:
            return self.parse_checkpoint_statement()
        elif token.type == TokenType.TIMELINE:
            return self.parse_timeline_statement()
        elif token.type == TokenType.MERGE:
            return self.parse_merge_statement()
        elif token.type == TokenType.UNDO:
            return self.parse_undo_statement()
        elif token.type == TokenType.NEWLINE:
            self.advance()
            return None
        else:
            raise SyntaxError(f"Unexpected token {token.type} at line {token.line}")
    
    def parse_dataset_declaration(self):
        self.expect(TokenType.DATASET)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.FROM)
        path = self.expect(TokenType.STRING).value
        
        versioned = False
        if self.current_token().type == TokenType.VERSIONED:
            self.advance()
            versioned = True
        
        return DatasetDeclaration(name, path, versioned)
    
    def parse_pipeline_definition(self):
        self.expect(TokenType.PIPELINE)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)
        self.skip_newlines()
        
        body = []
        while self.current_token().type != TokenType.END:
            if self.current_token().type == TokenType.FROM:
                body.append(self.parse_from_clause())
            elif self.current_token().type == TokenType.WHERE:
                body.append(self.parse_where_clause())
            elif self.current_token().type == TokenType.JOIN:
                body.append(self.parse_join_clause())
            elif self.current_token().type == TokenType.DERIVE:
                body.append(self.parse_derive_clause())
            elif self.current_token().type == TokenType.FEATURES:
                body.append(self.parse_features_clause())
            elif self.current_token().type == TokenType.TARGET:
                body.append(self.parse_target_clause())
            elif self.current_token().type == TokenType.SPLIT:
                body.append(self.parse_split_clause())
            elif self.current_token().type == TokenType.NEWLINE:
                self.advance()
            else:
                raise SyntaxError(f"Unexpected token in pipeline: {self.current_token().type} at line {self.current_token().line}")
        
        self.expect(TokenType.END)
        return PipelineDefinition(name, body)
    
    def parse_from_clause(self):
        self.expect(TokenType.FROM)
        dataset_name = self.expect(TokenType.IDENTIFIER).value
        return FromClause(dataset_name)
    
    def parse_where_clause(self):
        self.expect(TokenType.WHERE)
        condition = self.parse_expression()
        return WhereClause(condition)
    
    def parse_join_clause(self):
        self.expect(TokenType.JOIN)
        dataset_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.ON)
        condition = self.parse_expression()
        return JoinClause(dataset_name, condition)
    
    def parse_derive_clause(self):
        self.expect(TokenType.DERIVE)
        variable = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.EQUALS)
        expression = self.parse_expression()
        return DeriveClause(variable, expression)
    
    def parse_features_clause(self):
        self.expect(TokenType.FEATURES)
        self.expect(TokenType.LBRACKET)
        
        features = []
        while self.current_token().type != TokenType.RBRACKET:
            features.append(self.expect(TokenType.IDENTIFIER).value)
            if self.current_token().type == TokenType.COMMA:
                self.advance()
        
        self.expect(TokenType.RBRACKET)
        return FeaturesClause(features)
    
    def parse_target_clause(self):
        self.expect(TokenType.TARGET)
        target_name = self.expect(TokenType.IDENTIFIER).value
        return TargetClause(target_name)
    
    def parse_split_clause(self):
        self.expect(TokenType.SPLIT)
        train_percent = self.expect(TokenType.NUMBER).value
        self.expect(TokenType.PERCENT)
        self.expect(TokenType.IDENTIFIER)  # "train"
        self.expect(TokenType.COMMA)
        test_percent = self.expect(TokenType.NUMBER).value
        self.expect(TokenType.PERCENT)
        self.expect(TokenType.IDENTIFIER)  # "test"
        return SplitClause(train_percent, test_percent)
    
    def parse_experiment_definition(self):
        self.expect(TokenType.EXPERIMENT)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)
        self.skip_newlines()
        
        self.expect(TokenType.MODEL)
        model_type = self.expect(TokenType.IDENTIFIER).value
        self.skip_newlines()
        
        self.expect(TokenType.USING)
        pipeline_name = self.expect(TokenType.IDENTIFIER).value
        self.skip_newlines()
        
        self.expect(TokenType.METRICS)
        self.expect(TokenType.LBRACKET)
        
        metrics = []
        while self.current_token().type != TokenType.RBRACKET:
            metrics.append(self.expect(TokenType.IDENTIFIER).value)
            if self.current_token().type == TokenType.COMMA:
                self.advance()
        
        self.expect(TokenType.RBRACKET)
        self.skip_newlines()
        self.expect(TokenType.END)
        
        return ExperimentDefinition(name, model_type, pipeline_name, metrics)
    
    def parse_print_statement(self):
        self.expect(TokenType.PRINT)
        what = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.OF)
        of = self.expect(TokenType.IDENTIFIER).value
        return PrintStatement(what, of)
    
    def parse_checkpoint_statement(self):
        self.expect(TokenType.CHECKPOINT)
        name = self.expect(TokenType.STRING).value
        return CheckpointStatement(name)
    
    def parse_timeline_statement(self):
        self.expect(TokenType.TIMELINE)
        name = self.expect(TokenType.STRING).value
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        
        body = []
        while self.current_token().type != TokenType.RBRACE:
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()
        
        self.expect(TokenType.RBRACE)
        return TimelineStatement(name, body)
    
    def parse_merge_statement(self):
        self.expect(TokenType.MERGE)
        source = self.expect(TokenType.STRING).value
        self.expect(TokenType.INTO)
        target = self.expect(TokenType.STRING).value
        return MergeStatement(source, target)
    
    def parse_undo_statement(self):
        self.expect(TokenType.UNDO)
        name = self.expect(TokenType.STRING).value
        return UndoStatement(name)
    
    def parse_expression(self):
        return self.parse_or_expression()
    
    def parse_or_expression(self):
        left = self.parse_and_expression()
        
        while self.current_token().type == TokenType.OR:
            op = self.current_token().value
            self.advance()
            right = self.parse_and_expression()
            left = BinaryOp(left, op, right)
        
        return left
    
    def parse_and_expression(self):
        left = self.parse_comparison_expression()
        
        while self.current_token().type == TokenType.AND:
            op = self.current_token().value
            self.advance()
            right = self.parse_comparison_expression()
            left = BinaryOp(left, op, right)
        
        return left
    
    def parse_comparison_expression(self):
        left = self.parse_additive_expression()
        
        while self.current_token().type in (TokenType.DOUBLE_EQUALS, TokenType.NOT_EQUALS,
                                            TokenType.LESS_THAN, TokenType.GREATER_THAN,
                                            TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            op = self.current_token().value
            self.advance()
            right = self.parse_additive_expression()
            left = BinaryOp(left, op, right)
        
        return left
    
    def parse_additive_expression(self):
        left = self.parse_multiplicative_expression()
        
        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token().value
            self.advance()
            right = self.parse_multiplicative_expression()
            left = BinaryOp(left, op, right)
        
        return left
    
    def parse_multiplicative_expression(self):
        left = self.parse_unary_expression()
        
        while self.current_token().type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            op = self.current_token().value
            self.advance()
            right = self.parse_unary_expression()
            left = BinaryOp(left, op, right)
        
        return left
    
    def parse_unary_expression(self):
        if self.current_token().type == TokenType.NOT:
            op = self.current_token().value
            self.advance()
            operand = self.parse_unary_expression()
            return UnaryOp(op, operand)
        
        return self.parse_primary_expression()
    
    def parse_primary_expression(self):
        token = self.current_token()
        
        if token.type == TokenType.NUMBER:
            self.advance()
            return Literal(token.value)
        elif token.type == TokenType.STRING:
            self.advance()
            return Literal(token.value)
        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            expr = Identifier(token.value)
            
            # Handle member access
            while self.current_token().type == TokenType.DOT:
                self.advance()
                member = self.expect(TokenType.IDENTIFIER).value
                expr = MemberAccess(expr, member)
            
            return expr
        elif token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        else:
            raise SyntaxError(f"Unexpected token in expression: {token.type} at line {token.line}")
