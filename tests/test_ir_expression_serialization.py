"""Regression tests for IR expression serialization correctness.

These pin the two Codex P1 bugs:
1. `_maybe_parenthesize` must preserve parens for same-precedence
   non-associative operators on the right side.
2. Unary `not` must parenthesize binary operands."""

from fusionflow.ast_nodes import BinaryOp, Identifier, Literal, UnaryOp
from fusionflow.ir_export import _expression_to_string


def _id(name: str) -> Identifier:
    return Identifier(name)


def test_subtraction_right_grouping_preserved():
    """a - (b - c) must NOT collapse to 'a - b - c'."""
    # a - (b - c)
    expr = BinaryOp(_id("a"), "-", BinaryOp(_id("b"), "-", _id("c")))
    assert _expression_to_string(expr) == "a - (b - c)"


def test_division_right_grouping_preserved():
    """a / (b / c) must NOT collapse to 'a / b / c'."""
    expr = BinaryOp(_id("a"), "/", BinaryOp(_id("b"), "/", _id("c")))
    assert _expression_to_string(expr) == "a / (b / c)"


def test_subtraction_of_sum_right_grouping():
    """a - (b + c) must NOT collapse to 'a - b + c' (same precedence, non-associative parent)."""
    expr = BinaryOp(_id("a"), "-", BinaryOp(_id("b"), "+", _id("c")))
    assert _expression_to_string(expr) == "a - (b + c)"


def test_division_of_product_right_grouping():
    """a / (b * c) must NOT collapse to 'a / b * c'."""
    expr = BinaryOp(_id("a"), "/", BinaryOp(_id("b"), "*", _id("c")))
    assert _expression_to_string(expr) == "a / (b * c)"


def test_left_grouping_unchanged_for_associative_ops():
    """(a + b) + c is the same as a + b + c; left-associative grouping needs no parens."""
    expr = BinaryOp(BinaryOp(_id("a"), "+", _id("b")), "+", _id("c"))
    assert _expression_to_string(expr) == "a + b + c"


def test_left_side_subtraction_no_extra_parens():
    """(a - b) - c is the same as a - b - c. Left side of same-precedence op = no parens."""
    expr = BinaryOp(BinaryOp(_id("a"), "-", _id("b")), "-", _id("c"))
    assert _expression_to_string(expr) == "a - b - c"


def test_not_binary_expression_parenthesized():
    """not (a and b) must NOT collapse to 'not a and b' (which Python evaluates as (not a) and b)."""
    expr = UnaryOp("not", BinaryOp(_id("a"), "and", _id("b")))
    assert _expression_to_string(expr) == "not (a and b)"


def test_not_or_expression_parenthesized():
    """not (a or b) must preserve parens."""
    expr = UnaryOp("not", BinaryOp(_id("a"), "or", _id("b")))
    assert _expression_to_string(expr) == "not (a or b)"


def test_not_comparison_parenthesized():
    """not (a > b) must preserve parens (even though > binds tighter than `not` in Python)."""
    expr = UnaryOp("not", BinaryOp(_id("a"), ">", Literal(0)))
    assert _expression_to_string(expr) == "not (a > 0)"


def test_not_identifier_not_parenthesized():
    """not a (no binary operand) needs no parens."""
    expr = UnaryOp("not", _id("a"))
    assert _expression_to_string(expr) == "not a"


def test_lower_precedence_child_still_parenthesized_on_left():
    """(a + b) * c — child has lower precedence, must be parenthesized."""
    expr = BinaryOp(BinaryOp(_id("a"), "+", _id("b")), "*", _id("c"))
    assert _expression_to_string(expr) == "(a + b) * c"


def test_lower_precedence_child_still_parenthesized_on_right():
    """c * (a + b) — child has lower precedence on right, must be parenthesized."""
    expr = BinaryOp(_id("c"), "*", BinaryOp(_id("a"), "+", _id("b")))
    assert _expression_to_string(expr) == "c * (a + b)"


def test_full_roundtrip_via_parser():
    """Real end-to-end: parse a .ff with a tricky expression, serialize, expect the right text."""
    from fusionflow.interpreter import Interpreter
    from fusionflow.ir_export import build_temporal_ir
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    # Parser produces a - (b - c) when source has explicit parens
    source = """
    dataset d v1
        source "x.csv"
    end
    pipeline p
        from d v1
        derive y = a - (b - c)
        target y
    end
    """
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    ir = build_temporal_ir(runtime)
    derive_op = ir["pipelines"]["p"]["operations"][0]
    assert derive_op["type"] == "derive"
    # The serialized expression must preserve the right-side grouping
    assert derive_op["expression"] == "a - (b - c)"


def test_full_roundtrip_not_and_via_parser():
    """End-to-end: `where not (a and b)` must serialize with parens preserved."""
    from fusionflow.interpreter import Interpreter
    from fusionflow.ir_export import build_temporal_ir
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    source = """
    dataset d v1
        source "x.csv"
    end
    pipeline p
        from d v1
        derive ok = not (a and b)
        target ok
    end
    """
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    ir = build_temporal_ir(runtime)
    derive_op = ir["pipelines"]["p"]["operations"][0]
    assert derive_op["expression"] == "not (a and b)"
