"""Expression evaluation (left to right, no short-circuiting)."""

from robot_ide.core.enums import Operator
from robot_ide.core.exceptions import BadArgError, BadOperandError
from robot_ide.core.models import MineValue, format_value, is_boolean_value, is_integer_value
from robot_ide.interpreter.execution_context import ExecutionContext
from robot_ide.parser.ast_nodes import (
    BinaryNode,
    ExpressionNode,
    IsThereNode,
    LiteralNode,
    UnaryNode,
    VariableNode,
)

_ARITHMETIC = {
    Operator.ADD: lambda left, right: left + right,
    Operator.SUBTRACT: lambda left, right: left - right,
    Operator.MULTIPLY: lambda left, right: left * right,
}
_COMPARISON = {
    Operator.LESS: lambda left, right: left < right,
    Operator.LESS_EQUAL: lambda left, right: left <= right,
    Operator.GREATER: lambda left, right: left > right,
    Operator.GREATER_EQUAL: lambda left, right: left >= right,
}


class Evaluator:
    """Evaluates expression nodes against an execution context."""

    def __init__(self, context: ExecutionContext) -> None:
        self._context = context

    def evaluate(self, node: ExpressionNode) -> MineValue:
        """Evaluate any expression node."""
        if isinstance(node, LiteralNode):
            return node.value
        if isinstance(node, VariableNode):
            return self._context.environment.get(node.name)
        if isinstance(node, UnaryNode):
            return self._evaluate_not(node)
        if isinstance(node, BinaryNode):
            return self._evaluate_binary(node)
        if isinstance(node, IsThereNode):
            return self._evaluate_is_there(node)
        raise TypeError(f"unsupported expression node: {type(node).__name__}")

    def evaluate_integer_argument(self, node: ExpressionNode, apiName: str) -> int:
        """Evaluate an API argument; log name and value; require an integer."""
        self._context.logger.add_part(apiName)
        value = self.evaluate(node)
        self._context.logger.add_part(format_value(value))
        if not is_integer_value(value):
            raise BadArgError(f"{apiName} expects an integer argument")
        assert isinstance(value, int)
        return value

    def _evaluate_not(self, node: UnaryNode) -> bool:
        operand = self.evaluate(node.operand)
        if not is_boolean_value(operand):
            raise BadOperandError("'not' needs a boolean operand")
        return not bool(operand)

    def _evaluate_binary(self, node: BinaryNode) -> MineValue:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        operator = node.operator
        if operator in (Operator.EQUAL, Operator.NOT_EQUAL):
            if type(left) is not type(right):
                raise BadOperandError("equality needs operands of the same type")
            return (left == right) == (operator is Operator.EQUAL)
        if operator in (Operator.AND, Operator.OR):
            if not (is_boolean_value(left) and is_boolean_value(right)):
                raise BadOperandError(f"'{operator.value}' needs boolean operands")
            return bool(left and right) if operator is Operator.AND else bool(left or right)
        if not (is_integer_value(left) and is_integer_value(right)):
            raise BadOperandError(f"'{operator.value}' needs integer operands")
        assert isinstance(left, int) and isinstance(right, int)
        if operator in _ARITHMETIC:
            return _ARITHMETIC[operator](left, right)
        return _COMPARISON[operator](left, right)

    def _evaluate_is_there(self, node: IsThereNode) -> bool:
        cellKind = self.evaluate_integer_argument(node.argument, "isThere")
        result = self._context.sensor.is_there(cellKind)
        self._context.logger.add_part(format_value(result))
        return result
