"""Interpreter facade: wires context, evaluator and executor to a simulation."""

from collections.abc import Iterator, Sequence

from robot_ide.core.constants import MAX_EXECUTED_LINES
from robot_ide.core.enums import RunStatus
from robot_ide.core.exceptions import InstructionLimitExceededError, MineRuntimeError
from robot_ide.interpreter.environment import Environment
from robot_ide.interpreter.evaluator import Evaluator
from robot_ide.interpreter.execution_context import ExecutionContext
from robot_ide.interpreter.executor import Executor
from robot_ide.logging.execution_logger import ExecutionLogger
from robot_ide.parser.ast_nodes import StatementNode
from robot_ide.simulator.robot import Robot
from robot_ide.simulator.sensor import Sensor
from robot_ide.simulator.simulation_state import SimulationState


class Interpreter:
    """Runs one program against one simulation, logging into the given logger."""

    def __init__(
        self,
        program: Sequence[StatementNode],
        simulation: SimulationState,
        logger: ExecutionLogger,
        maxExecutedLines: int = MAX_EXECUTED_LINES,
    ) -> None:
        self._program = list(program)
        self._logger = logger
        self.context = ExecutionContext(
            Environment(), Robot(simulation), Sensor(simulation), logger, maxExecutedLines
        )
        self._executor = Executor(self.context, Evaluator(self.context))
        self.status: RunStatus | None = None
        self.error: MineRuntimeError | None = None

    def steps(self) -> Iterator[int]:
        """Run lazily; yields each source line right before it executes.

        After the iterator ends, ``status`` and ``error`` describe the outcome and the log
        is closed (``EOR``, an error code or the limit marker).
        """
        self._logger.reset()
        try:
            yield from self._executor.execute_block(self._program)
        except InstructionLimitExceededError:
            self._logger.log_limit_exceeded()
            self.status = RunStatus.LIMIT_EXCEEDED
        except MineRuntimeError as error:
            error.attach_line(self.context.currentLine)
            self._logger.log_error(error.errorCode)
            self.error = error
            self.status = RunStatus.RUNTIME_ERROR
        else:
            self._logger.log_end_of_run()
            self.status = RunStatus.COMPLETED

    def run(self) -> RunStatus:
        """Run to the end and return the final status."""
        for _ in self.steps():
            pass
        assert self.status is not None
        return self.status
