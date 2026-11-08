"""Shared test helpers."""

from robot_ide.services.execution_service import ExecutionResult, ExecutionService


def run_program(mapText: str, programText: str = "") -> ExecutionResult:
    """Run a map plus a program given as separate strings."""
    mapLines = mapText.strip("\n").splitlines()
    header = f"{len(mapLines)} {len(mapLines[0])}"
    inputText = "\n".join([header, *mapLines, *programText.splitlines()])
    return ExecutionService().run_text(inputText)


def log_lines(result: ExecutionResult) -> list[str]:
    """Log of a result as a list of lines."""
    return result.logText.splitlines()
