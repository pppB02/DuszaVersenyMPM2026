"""Step-wise program run used by the debugger and the automatic runner (no Qt here)."""

from collections.abc import Iterator

from robot_ide.core.constants import MAX_EXECUTED_LINES
from robot_ide.core.enums import RunStatus
from robot_ide.core.exceptions import MineRuntimeError, MineScriptSyntaxError
from robot_ide.core.models import MineValue
from robot_ide.interpreter.interpreter import Interpreter
from robot_ide.logging.execution_logger import ExecutionLogger
from robot_ide.parser.parser import parse_source
from robot_ide.simulator.simulation_state import SimulationState


class DebugSession:
    """One run of a program against a simulation, advanced one source line at a time.

    ``currentLine`` is the line that executes on the next ``step()``. After ``start()`` it is
    the first line and nothing has run yet.
    """

    def __init__(
        self, simulation: SimulationState, maxExecutedLines: int = MAX_EXECUTED_LINES
    ) -> None:
        self.simulation = simulation
        self._maxExecutedLines = maxExecutedLines
        self._iterator: Iterator[int] | None = None
        self._interpreter: Interpreter | None = None
        self._logger = ExecutionLogger()
        self.currentLine: int | None = None
        self.status: RunStatus | None = None
        self.syntaxError: MineScriptSyntaxError | None = None

    def set_simulation(self, simulation: SimulationState) -> None:
        """Use another simulation (after loading a new map)."""
        self.stop()
        self.simulation = simulation
        self._interpreter = None
        self._logger = ExecutionLogger()
        self.status = None
        self.currentLine = None
        self.syntaxError = None

    def start(self, programText: str) -> None:
        """Reset the simulation and prepare a fresh run; stops at the first line."""
        self.stop()
        self.simulation.reset()
        self._logger = ExecutionLogger()
        self.syntaxError = None
        self.currentLine = None
        self.status = None
        try:
            program = parse_source(programText.splitlines())
        except MineScriptSyntaxError as error:
            self.syntaxError = error
            self.status = RunStatus.SYNTAX_ERROR
            self._interpreter = None
            return
        self._interpreter = Interpreter(
            program, self.simulation, self._logger, self._maxExecutedLines
        )
        self._iterator = self._interpreter.steps()
        self._advance()

    def step(self) -> bool:
        """Execute the current line. Returns True if the run can continue."""
        if self._iterator is None:
            return False
        self._advance()
        return self._iterator is not None

    def stop(self) -> None:
        """Abort an active run (the log keeps what was recorded so far)."""
        if self._iterator is not None:
            self._iterator.close()
            self._iterator = None
            self.currentLine = None
            self.status = RunStatus.STOPPED

    def _advance(self) -> None:
        assert self._iterator is not None and self._interpreter is not None
        try:
            self.currentLine = next(self._iterator)
        except StopIteration:
            self.currentLine = None
            self._iterator = None
            self.status = self._interpreter.status

    @property
    def is_active(self) -> bool:
        """True while lines remain to be executed."""
        return self._iterator is not None

    @property
    def runtimeError(self) -> MineRuntimeError | None:
        """The runtime error that ended the run, if any."""
        return self._interpreter.error if self._interpreter is not None else None

    @property
    def variables(self) -> dict[str, MineValue]:
        """Current variable values."""
        if self._interpreter is None:
            return {}
        return self._interpreter.context.environment.snapshot()

    @property
    def printedOutput(self) -> list[str]:
        """Everything printed so far."""
        return [] if self._interpreter is None else list(self._interpreter.context.printedOutput)

    @property
    def executedLines(self) -> int:
        """Lines whose execution is complete."""
        if self._interpreter is None:
            return 0
        count = self._interpreter.context.executedCount
        return count - 1 if self.currentLine is not None else count

    @property
    def logText(self) -> str:
        """Run log so far."""
        return self._logger.to_text()
