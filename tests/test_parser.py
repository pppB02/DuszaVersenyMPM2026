import pytest

from robot_ide.core.enums import Operator
from robot_ide.core.exceptions import MineScriptSyntaxError
from robot_ide.parser.ast_nodes import (
    BinaryNode,
    IfNode,
    IsThereNode,
    LiteralNode,
    MineHereNode,
    PrintNode,
    SetNode,
    StepForwardNode,
    TurnByNode,
    UnaryNode,
    VariableNode,
    WhileNode,
)
from robot_ide.parser.parser import parse_source
from robot_ide.parser.syntax_validator import control_depth, is_valid_identifier


def test_empty_program_is_valid() -> None:
    assert parse_source([]) == []
    assert parse_source(["", "   "]) == []


def test_simple_statements() -> None:
    program = parse_source(
        ["set a to 5", "step forward 2", "turn by 1", "mine here", "print a", "print true"]
    )
    kinds = [type(node) for node in program]
    assert kinds == [SetNode, StepForwardNode, TurnByNode, MineHereNode, PrintNode, PrintNode]


def test_set_expression_forms() -> None:
    program = parse_source(
        ["set a to 1", "set b to a + 1", "set c to not b", "set d to isThere 2", "set e to a <> 2"]
    )
    expressions = [node.expression for node in program if isinstance(node, SetNode)]
    assert expressions[0] == LiteralNode(1, 1)
    assert isinstance(expressions[1], BinaryNode) and expressions[1].operator is Operator.ADD
    assert isinstance(expressions[2], UnaryNode)
    assert isinstance(expressions[3], IsThereNode)
    assert isinstance(expressions[4], BinaryNode) and expressions[4].operator is Operator.NOT_EQUAL
    assert expressions[1].left == VariableNode(2, "a")


def test_if_else_structure_and_else_line() -> None:
    program = parse_source(["if x", "  print 1", "else", "  print 2", "print 3"])
    node = program[0]
    assert isinstance(node, IfNode)
    assert len(node.thenBody) == 1 and node.elseBody is not None and len(node.elseBody) == 1
    assert node.elseLineNumber == 3
    assert len(program) == 2


def test_while_and_nesting_with_line_numbers() -> None:
    program = parse_source(
        ["", "while true", "  if a", "    while b", "      print 1", "  print 2", "print 3"]
    )
    outer = program[0]
    assert isinstance(outer, WhileNode) and outer.lineNumber == 2
    inner = outer.body[0]
    assert isinstance(inner, IfNode) and inner.lineNumber == 3
    assert inner.thenBody[0].lineNumber == 4
    assert outer.body[1].lineNumber == 6
    assert program[1].lineNumber == 7
    assert control_depth(program) == 3


def test_else_belongs_to_same_level_if() -> None:
    program = parse_source(
        ["if a", "  if b", "    print 1", "  else", "    print 2", "else", "  print 3"]
    )
    outer = program[0]
    assert isinstance(outer, IfNode) and outer.elseBody is not None
    inner = outer.thenBody[0]
    assert isinstance(inner, IfNode) and inner.elseBody is not None
    assert inner.elseLineNumber == 4 and outer.elseLineNumber == 6


@pytest.mark.parametrize(
    "lines",
    [
        ["\tprint 1"],  # tab indentation
        ["  print 1"],  # indent without block
        ["if a"],  # missing block
        ["if a", "print 1"],  # block not indented
        ["while a", "    print 1", "  print 2"],  # inconsistent dedent
        ["else", "  print 1"],  # else without if
        ["print 1", "else", "  print 2"],  # else without if
        ["set 9lives to 1"],  # bad identifier
        ["set if to 1"],  # keyword as name
        ["set a 1"],  # missing 'to'
        ["step 1"],  # missing 'forward'
        ["mine"],  # incomplete
        ["print"],  # missing expression
        ["set a to 1 +"],  # bad expression
        ["print a+1"],  # no spaces -> invalid token
        ["jump 3"],  # unknown statement
        ["set a to 101"],  # number out of range
    ],
)
def test_syntax_errors(lines: list[str]) -> None:
    with pytest.raises(MineScriptSyntaxError):
        parse_source(lines)


def test_identifier_rules() -> None:
    assert is_valid_identifier("arany")
    assert is_valid_identifier("szám_2")
    assert not is_valid_identifier("9lives")
    assert not is_valid_identifier("while")
    assert not is_valid_identifier("")
