"""Parser for the FusionFlow temporal specification language"""

from .tokens import Token, TokenType
from .ast_nodes import (
    Program,
    DatasetDeclaration,
    DatasetReference,
    SchemaField,
    PipelineDefinition,
    DeriveStep,
    SelectStep,
    TargetStep,
    PipelineExtension,
    ModelDefinition,
    ExperimentDefinition,
    TimelineDefinition,
    MergeStrategy,
    MergeStatement,
    BinaryOp,
    UnaryOp,
    Literal,
    Identifier,
    MemberAccess,
)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

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

    def expect_any(self, *token_types):
        token = self.current_token()
        if token.type not in token_types:
            expected = ', '.join(t.name for t in token_types)
            raise SyntaxError(f"Expected one of ({expected}), got {token.type} at line {token.line}")
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
        if token.type == TokenType.PIPELINE:
            return self.parse_pipeline_definition()
        if token.type == TokenType.MODEL:
            return self.parse_model_definition()
        if token.type == TokenType.EXPERIMENT:
            return self.parse_experiment_definition()
        if token.type == TokenType.TIMELINE:
            return self.parse_timeline_definition()
        if token.type == TokenType.MERGE:
            return self.parse_merge_statement()
        if token.type == TokenType.NEWLINE:
            self.advance()
            return None

        raise SyntaxError(f"Unexpected token {token.type} at line {token.line}")

    def parse_dataset_declaration(self):
        self.expect(TokenType.DATASET)
        name = self.expect(TokenType.IDENTIFIER).value
        version_token = self.expect_any(TokenType.IDENTIFIER, TokenType.STRING)
        version = version_token.value
        self.skip_newlines()

        source = None
        description = None
        schema_fields = []

        while self.current_token().type != TokenType.END:
            token = self.current_token()
            if token.type == TokenType.SOURCE:
                self.advance()
                source = self.expect(TokenType.STRING).value
                self.skip_newlines()
            elif token.type == TokenType.DESCRIPTION:
                self.advance()
                description = self.expect(TokenType.STRING).value
                self.skip_newlines()
            elif token.type == TokenType.SCHEMA:
                schema_fields = self.parse_schema_block()
                self.skip_newlines()
            elif token.type == TokenType.NEWLINE:
                self.advance()
            else:
                raise SyntaxError(f"Unexpected token {token.type} in dataset declaration at line {token.line}")

        self.expect(TokenType.END)

        if source is None:
            raise SyntaxError(f"Dataset '{name}' is missing a source declaration")

        return DatasetDeclaration(name=name, version=version, source=source, schema=schema_fields, description=description)

    def parse_schema_block(self):
        self.expect(TokenType.SCHEMA)
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        fields = []
        while self.current_token().type != TokenType.RBRACE:
            field_name = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.COLON)
            type_token = self.expect(TokenType.IDENTIFIER)
            fields.append(SchemaField(field_name, type_token.value))

            if self.current_token().type == TokenType.COMMA:
                self.advance()
            if self.current_token().type == TokenType.NEWLINE:
                self.skip_newlines()

        self.expect(TokenType.RBRACE)
        return fields

    def parse_pipeline_definition(self):
        self.expect(TokenType.PIPELINE)
        name = self.expect(TokenType.IDENTIFIER).value
        self.skip_newlines()

        source = None
        steps = []

        while self.current_token().type != TokenType.END:
            token = self.current_token()
            if token.type == TokenType.FROM:
                if source is not None:
                    raise SyntaxError(f"Pipeline '{name}' has multiple from clauses")
                source = self.parse_pipeline_source()
                self.skip_newlines()
            elif token.type == TokenType.DERIVE:
                steps.append(self.parse_derive_step())
                self.skip_newlines()
            elif token.type == TokenType.SELECT:
                steps.append(self.parse_select_step())
                self.skip_newlines()
            elif token.type == TokenType.TARGET:
                steps.append(self.parse_target_step())
                self.skip_newlines()
            elif token.type == TokenType.NEWLINE:
                self.advance()
            else:
                raise SyntaxError(f"Unexpected token {token.type} in pipeline definition at line {token.line}")

        self.expect(TokenType.END)

        if source is None:
            raise SyntaxError(f"Pipeline '{name}' is missing a from clause")

        return PipelineDefinition(name=name, source=source, steps=steps)

    def parse_pipeline_source(self):
        self.expect(TokenType.FROM)
        dataset = self.expect(TokenType.IDENTIFIER).value
        version_token = self.expect_any(TokenType.IDENTIFIER, TokenType.STRING)
        version = version_token.value
        return DatasetReference(dataset, version)

    def parse_derive_step(self):
        self.expect(TokenType.DERIVE)
        variable = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.EQUALS)
        expression = self.parse_expression()
        return DeriveStep(variable, expression)

    def parse_select_step(self):
        self.expect(TokenType.SELECT)
        self.expect(TokenType.LBRACKET)

        fields = []
        while self.current_token().type != TokenType.RBRACKET:
            token = self.expect(TokenType.IDENTIFIER)
            fields.append(token.value)
            if self.current_token().type == TokenType.COMMA:
                self.advance()
            elif self.current_token().type == TokenType.NEWLINE:
                self.skip_newlines()

        self.expect(TokenType.RBRACKET)
        return SelectStep(fields)

    def parse_target_step(self):
        self.expect(TokenType.TARGET)
        target_name = self.expect(TokenType.IDENTIFIER).value
        return TargetStep(target_name)

    def parse_model_definition(self):
        self.expect(TokenType.MODEL)
        name = self.expect(TokenType.IDENTIFIER).value
        self.skip_newlines()

        model_type = None
        params = {}

        while self.current_token().type != TokenType.END:
            token = self.current_token()
            if token.type == TokenType.TYPE:
                self.advance()
                model_type = self.expect(TokenType.IDENTIFIER).value
                self.skip_newlines()
            elif token.type == TokenType.PARAMS:
                params = self.parse_params_block()
                self.skip_newlines()
            elif token.type == TokenType.NEWLINE:
                self.advance()
            else:
                raise SyntaxError(f"Unexpected token {token.type} in model definition at line {token.line}")

        self.expect(TokenType.END)

        if model_type is None:
            raise SyntaxError(f"Model '{name}' is missing a type declaration")

        return ModelDefinition(name=name, type_name=model_type, params=params)

    def parse_params_block(self):
        self.expect(TokenType.PARAMS)
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        params = {}
        while self.current_token().type != TokenType.RBRACE:
            key = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.COLON)
            value = self.parse_expression()
            params[key] = value

            if self.current_token().type == TokenType.COMMA:
                self.advance()
            if self.current_token().type == TokenType.NEWLINE:
                self.skip_newlines()

        self.expect(TokenType.RBRACE)
        return params

    def parse_experiment_definition(self):
        self.expect(TokenType.EXPERIMENT)
        name = self.expect(TokenType.IDENTIFIER).value
        self.skip_newlines()

        description = None
        pipeline_name = None
        model_name = None
        metrics = []
        extension = None

        while self.current_token().type != TokenType.END:
            token = self.current_token()
            if token.type == TokenType.DESCRIPTION:
                self.advance()
                description = self.expect(TokenType.STRING).value
                self.skip_newlines()
            elif token.type == TokenType.USES:
                self.advance()
                binding_token = self.current_token()
                if binding_token.type == TokenType.PIPELINE:
                    self.advance()
                    pipeline_name = self.expect(TokenType.IDENTIFIER).value
                elif binding_token.type == TokenType.MODEL:
                    self.advance()
                    model_name = self.expect(TokenType.IDENTIFIER).value
                else:
                    binding_type = self.expect(TokenType.IDENTIFIER).value.lower()
                    if binding_type == 'pipeline':
                        pipeline_name = self.expect(TokenType.IDENTIFIER).value
                    elif binding_type == 'model':
                        model_name = self.expect(TokenType.IDENTIFIER).value
                    else:
                        raise SyntaxError(f"Unknown binding type '{binding_type}' in experiment '{name}'")
                self.skip_newlines()
            elif token.type == TokenType.METRICS:
                metrics = self.parse_metrics_list()
                self.skip_newlines()
            elif token.type == TokenType.EXTEND:
                extension = self.parse_extension_block()
                self.skip_newlines()
            elif token.type == TokenType.NEWLINE:
                self.advance()
            else:
                raise SyntaxError(f"Unexpected token {token.type} in experiment definition at line {token.line}")

        self.expect(TokenType.END)

        if pipeline_name is None:
            raise SyntaxError(f"Experiment '{name}' is missing a pipeline binding")
        if model_name is None:
            raise SyntaxError(f"Experiment '{name}' is missing a model binding")
        if not metrics:
            raise SyntaxError(f"Experiment '{name}' must declare at least one metric")

        return ExperimentDefinition(
            name=name,
            pipeline=pipeline_name,
            model=model_name,
            metrics=metrics,
            description=description,
            extension=extension,
        )

    def parse_metrics_list(self):
        self.expect(TokenType.METRICS)
        self.expect(TokenType.LBRACKET)

        metrics = []
        while self.current_token().type != TokenType.RBRACKET:
            metrics.append(self.expect(TokenType.IDENTIFIER).value)
            if self.current_token().type == TokenType.COMMA:
                self.advance()
            elif self.current_token().type == TokenType.NEWLINE:
                self.skip_newlines()

        self.expect(TokenType.RBRACKET)
        return metrics

    def parse_extension_block(self):
        self.expect(TokenType.EXTEND)
        self.expect(TokenType.LBRACE)
        self.skip_newlines()

        steps = []
        while self.current_token().type != TokenType.RBRACE:
            token = self.current_token()
            if token.type == TokenType.DERIVE:
                steps.append(self.parse_derive_step())
                self.skip_newlines()
            elif token.type == TokenType.SELECT:
                steps.append(self.parse_select_step())
                self.skip_newlines()
            elif token.type == TokenType.TARGET:
                steps.append(self.parse_target_step())
                self.skip_newlines()
            elif token.type == TokenType.NEWLINE:
                self.advance()
            else:
                raise SyntaxError(f"Unexpected token {token.type} in extension block at line {token.line}")

        self.expect(TokenType.RBRACE)
        return PipelineExtension(steps)

    def parse_timeline_definition(self):
        self.expect(TokenType.TIMELINE)
        name = self.expect(TokenType.IDENTIFIER).value

        description = None
        if self.current_token().type == TokenType.STRING:
            description = self.current_token().value
            self.advance()

        self.skip_newlines()

        experiments = []
        while self.current_token().type != TokenType.END:
            token = self.current_token()
            if token.type == TokenType.EXPERIMENT:
                experiments.append(self.parse_experiment_definition())
                self.skip_newlines()
            elif token.type == TokenType.NEWLINE:
                self.advance()
            else:
                raise SyntaxError(f"Unexpected token {token.type} in timeline definition at line {token.line}")

        self.expect(TokenType.END)
        return TimelineDefinition(name=name, description=description, experiments=experiments)

    def parse_merge_statement(self):
        self.expect(TokenType.MERGE)
        source = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.INTO)
        target = self.expect(TokenType.IDENTIFIER).value
        self.skip_newlines()

        justification = ""
        strategy = None

        while self.current_token().type != TokenType.END:
            token = self.current_token()
            if token.type == TokenType.BECAUSE:
                self.advance()
                justification = self.expect(TokenType.STRING).value
                self.skip_newlines()
            elif token.type == TokenType.STRATEGY:
                strategy = self.parse_strategy_spec()
                self.skip_newlines()
            elif token.type == TokenType.NEWLINE:
                self.advance()
            else:
                raise SyntaxError(f"Unexpected token {token.type} in merge statement at line {token.line}")

        self.expect(TokenType.END)

        if strategy is None:
            raise SyntaxError("Merge statements must declare a strategy")

        return MergeStatement(source_timeline=source, target_timeline=target, justification=justification, strategy=strategy)

    def parse_strategy_spec(self):
        self.expect(TokenType.STRATEGY)
        name = self.expect(TokenType.IDENTIFIER).value

        arguments = []
        while self.current_token().type in (TokenType.IDENTIFIER, TokenType.STRING):
            arguments.append(self.current_token().value)
            self.advance()

        return MergeStrategy(name=name, arguments=arguments)

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

        while self.current_token().type in (
            TokenType.DOUBLE_EQUALS,
            TokenType.NOT_EQUALS,
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_EQUAL,
        ):
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
        if token.type == TokenType.STRING:
            self.advance()
            return Literal(token.value)
        if token.type == TokenType.IDENTIFIER:
            self.advance()
            expr = Identifier(token.value)

            while self.current_token().type == TokenType.DOT:
                self.advance()
                member = self.expect(TokenType.IDENTIFIER).value
                expr = MemberAccess(expr, member)

            return expr
        if token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        raise SyntaxError(f"Unexpected token in expression: {token.type} at line {token.line}")
