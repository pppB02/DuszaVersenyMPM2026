"""AST node definitions. Every node keeps its 1-based program source line."""

from dataclasses import dataclass

from robot_ide.core.enums import Operator
from robot_ide.core.models import MineValue


@dataclass(frozen=True)
class ExpressionNode:
    """Base class of expressions. Expressions are flat: operands are literals or variables."""

    lineNumber: int


@dataclass(frozen=True)
class LiteralNode(ExpressionNode):
    """Integer or boolean constant."""

    value: MineValue


@dataclass(frozen=True)
class VariableNode(ExpressionNode):
    """Variable read."""

    name: str


@dataclass(frozen=True)
class UnaryNode(ExpressionNode):
    """``not operand``."""

    operator: Operator
    operand: ExpressionNode


@dataclass(frozen=True)
class BinaryNode(ExpressionNode):
    """``left operator right``."""

    operator: Operator
    left: ExpressionNode
    right: ExpressionNode


@dataclass(frozen=True)
class IsThereNode(ExpressionNode):
    """``isThere argument``."""

    argument: ExpressionNode


@dataclass(frozen=True)
class StatementNode:
    """Base class of statements."""

    lineNumber: int


@dataclass(frozen=True)
class SetNode(StatementNode):
    """``set name to expression``."""

    name: str
    expression: ExpressionNode


@dataclass(frozen=True)
class StepForwardNode(StatementNode):
    """``step forward expression``."""

    count: ExpressionNode


@dataclass(frozen=True)
class TurnByNode(StatementNode):
    """``turn by expression``."""

    count: ExpressionNode


@dataclass(frozen=True)
class MineHereNode(StatementNode):
    """``mine here``."""


@dataclass(frozen=True)
class PrintNode(StatementNode):
    """``print expression``."""

    expression: ExpressionNode


@dataclass(frozen=True)
class IfNode(StatementNode):
    """``if`` with optional ``else``. ``elseLineNumber`` is the source line of ``else``."""

    condition: ExpressionNode
    thenBody: list[StatementNode]
    elseBody: list[StatementNode] | None = None
    elseLineNumber: int | None = None


@dataclass(frozen=True)
class WhileNode(StatementNode):
    """``while`` loop."""

    condition: ExpressionNode
    body: list[StatementNode]
