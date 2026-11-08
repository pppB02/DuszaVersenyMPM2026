"""Statement execution as a generator, so callers can step, pause or stop between lines."""

from collections.abc import Iterator, Sequence

from robot_ide.core.exceptions import InstructionLimitExceededError, NonBoolConditionError
from robot_ide.core.models import format_value, is_boolean_value
from robot_ide.interpreter.evaluator import Evaluator
from robot_ide.interpreter.execution_context import ExecutionContext
from robot_ide.parser.ast_nodes import (
    ExpressionNode,
    IfNode,
    MineHereNode,
    PrintNode,
    SetNode,
    StatementNode,
    StepForwardNode,
    TurnByNode,
    WhileNode,
)


class Executor:
    """Runs statements. Each yielded value is the source line about to be executed."""

    def __init__(self, context: ExecutionContext, evaluator: Evaluator) -> None:
        self._context = context
        self._evaluator = evaluator

    def execute_block(self, statements: Sequence[StatementNode]) -> Iterator[int]:
        """Execute statements in order."""
        for statement in statements:
            yield from self._execute(statement)

    def _begin_line(self, lineNumber: int) -> None:
        """Count and log a line; enforce the central execution limit."""
        context = self._context
        if context.executedCount >= context.maxExecutedLines:
            raise InstructionLimitExceededError()
        context.executedCount += 1
        context.currentLine = lineNumber
        context.logger.begin_line(lineNumber)

    def _execute(self, statement: StatementNode) -> Iterator[int]:
        if isinstance(statement, IfNode):
            yield from self._execute_if(statement)
        elif isinstance(statement, WhileNode):
            yield from self._execute_while(statement)
        else:
            self._begin_line(statement.lineNumber)
            yield statement.lineNumber
            self._execute_simple(statement)

    def _execute_simple(self, statement: StatementNode) -> None:
        context = self._context
        if isinstance(statement, SetNode):
            value = self._evaluator.evaluate(statement.expression)
            context.environment.assign(statement.name, value)
        elif isinstance(statement, StepForwardNode):
            count = self._evaluator.evaluate_integer_argument(statement.count, "step forward")
            context.robot.step_forward(count)
        elif isinstance(statement, TurnByNode):
            count = self._evaluator.evaluate_integer_argument(statement.count, "turn by")
            context.robot.turn_by(count)
        elif isinstance(statement, MineHereNode):
            context.logger.add_part("mine here")
            context.robot.mine_here()
        elif isinstance(statement, PrintNode):
            self._execute_print(statement.expression)
        else:
            raise TypeError(f"unsupported statement node: {type(statement).__name__}")

    def _execute_print(self, expression: ExpressionNode) -> None:
        self._context.logger.add_part("print")
        value = self._evaluator.evaluate(expression)
        text = format_value(value)
        self._context.logger.add_part(text)
        self._context.printedOutput.append(text)

    def _evaluate_condition(self, condition: ExpressionNode) -> bool:
        value = self._evaluator.evaluate(condition)
        if not is_boolean_value(value):
            raise NonBoolConditionError("condition must be boolean")
        return bool(value)

    def _execute_if(self, node: IfNode) -> Iterator[int]:
        self._begin_line(node.lineNumber)
        yield node.lineNumber
        if self._evaluate_condition(node.condition):
            yield from self.execute_block(node.thenBody)
        elif node.elseBody is not None and node.elseLineNumber is not None:
            self._begin_line(node.elseLineNumber)
            yield node.elseLineNumber
            yield from self.execute_block(node.elseBody)

    def _execute_while(self, node: WhileNode) -> Iterator[int]:
        while True:
            self._begin_line(node.lineNumber)
            yield node.lineNumber
            if not self._evaluate_condition(node.condition):
                return
            yield from self.execute_block(node.body)
