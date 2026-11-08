"""End-to-end run: input text -> parse -> interpret -> log."""

from dataclasses import dataclass, field
from pathlib import Path

from robot_ide.core.constants import MAX_EXECUTED_LINES
from robot_ide.core.enums import RunStatus
from robot_ide.core.exceptions import MineRuntimeError, MineScriptSyntaxError
from robot_ide.interpreter.interpreter import Interpreter
from robot_ide.logging.execution_logger import ExecutionLogger
from robot_ide.parser.parser import parse_source
from robot_ide.services.file_service import load_input, read_text
from robot_ide.simulator.simulation_state import SimulationState


@dataclass
class ExecutionResult:
    """Outcome of one run."""

    status: RunStatus
    logText: str
    printedOutput: list[str] = field(default_factory=list)
    runtimeError: MineRuntimeError | None = None
    syntaxError: MineScriptSyntaxError | None = None
    simulation: SimulationState | None = None


class ExecutionService:
    """Runs MineScript programs; shared by CLI and (later) GUI."""

    def __init__(self, maxExecutedLines: int = MAX_EXECUTED_LINES) -> None:
        self._maxExecutedLines = maxExecutedLines

    def run_text(self, inputText: str) -> ExecutionResult:
        """Run a full input text (map + program)."""
        simulation, programInput = load_input(inputText)
        try:
            program = parse_source(programInput.programLines)
        except MineScriptSyntaxError as error:
            return ExecutionResult(
                RunStatus.SYNTAX_ERROR, "", syntaxError=error, simulation=simulation
            )
        logger = ExecutionLogger()
        interpreter = Interpreter(program, simulation, logger, self._maxExecutedLines)
        status = interpreter.run()
        return ExecutionResult(
            status,
            logger.to_text(),
            interpreter.context.printedOutput,
            interpreter.error,
            None,
            simulation,
        )

    def run_file(self, inputPath: Path, outputPath: Path) -> ExecutionResult:
        """Run an input file and write the log file (always overwritten first)."""
        outputPath.write_text("", encoding="utf-8")
        result = self.run_text(read_text(inputPath))
        outputPath.write_text(result.logText, encoding="utf-8")
        return result
