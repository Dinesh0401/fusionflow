"""AST node definitions for FusionFlow"""

from dataclasses import dataclass
from typing import Any, List, Optional

@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]

@dataclass
class DatasetDeclaration(ASTNode):
    name: str
    path: str
    versioned: bool = False

@dataclass
class PipelineDefinition(ASTNode):
    name: str
    body: List[ASTNode]

@dataclass
class FromClause(ASTNode):
    dataset_name: str

@dataclass
class WhereClause(ASTNode):
    condition: 'Expression'

@dataclass
class JoinClause(ASTNode):
    dataset_name: str
    condition: 'Expression'

@dataclass
class DeriveClause(ASTNode):
    variable: str
    expression: 'Expression'

@dataclass
class FeaturesClause(ASTNode):
    feature_list: List[str]

@dataclass
class TargetClause(ASTNode):
    target_name: str

@dataclass
class SplitClause(ASTNode):
    train_percent: float
    test_percent: float

@dataclass
class ExperimentDefinition(ASTNode):
    name: str
    model_type: str
    pipeline_name: str
    metrics: List[str]

@dataclass
class PrintStatement(ASTNode):
    what: str
    of: str

@dataclass
class CheckpointStatement(ASTNode):
    name: str

@dataclass
class TimelineStatement(ASTNode):
    name: str
    body: List[ASTNode]

@dataclass
class MergeStatement(ASTNode):
    source_timeline: str
    target_timeline: str

@dataclass
class UndoStatement(ASTNode):
    checkpoint_name: str

# Expression nodes
@dataclass
class Expression(ASTNode):
    pass

@dataclass
class BinaryOp(Expression):
    left: Expression
    operator: str
    right: Expression

@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression

@dataclass
class Literal(Expression):
    value: Any

@dataclass
class Identifier(Expression):
    name: str

@dataclass
class MemberAccess(Expression):
    object: Expression
    member: str
