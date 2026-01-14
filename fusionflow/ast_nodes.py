"""AST node definitions for FusionFlow"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]

@dataclass
class SchemaField(ASTNode):
    name: str
    type_name: str

@dataclass
class DatasetDeclaration(ASTNode):
    name: str
    version: str
    source: str
    schema: List[SchemaField]
    description: Optional[str] = None

@dataclass
class DatasetReference(ASTNode):
    name: str
    version: str

@dataclass
class PipelineStep(ASTNode):
    pass

@dataclass
class DeriveStep(PipelineStep):
    variable: str
    expression: 'Expression'

@dataclass
class SelectStep(PipelineStep):
    fields: List[str]

@dataclass
class TargetStep(PipelineStep):
    field: str

@dataclass
class PipelineDefinition(ASTNode):
    name: str
    source: DatasetReference
    steps: List[PipelineStep]

@dataclass
class PipelineExtension(ASTNode):
    steps: List[PipelineStep]

@dataclass
class ModelDefinition(ASTNode):
    name: str
    type_name: str
    params: Dict[str, Any]

@dataclass
class ExperimentDefinition(ASTNode):
    name: str
    pipeline: str
    model: str
    metrics: List[str]
    description: Optional[str] = None
    extension: Optional[PipelineExtension] = None

@dataclass
class TimelineDefinition(ASTNode):
    name: str
    description: Optional[str]
    experiments: List[ExperimentDefinition]

@dataclass
class MergeStrategy(ASTNode):
    name: str
    arguments: List[str]

@dataclass
class MergeStatement(ASTNode):
    source_timeline: str
    target_timeline: str
    justification: str
    strategy: MergeStrategy

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
