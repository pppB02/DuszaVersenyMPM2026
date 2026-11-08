"""Command line entry: ``main.py [-q] [input [output]]``."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from robot_ide.core.enums import RunStatus
from robot_ide.core.exceptions import InputFormatError
from robot_ide.services.execution_service import ExecutionService


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(prog="robot")
    parser.add_argument("-q", "--quiet", action="store_true", help="run without GUI")
    parser.add_argument("inputFile", type=Path, nargs="?")
    parser.add_argument("outputFile", type=Path, nargs="?")
    return parser


def run_quiet(inputFile: Path, outputFile: Path) -> int:
    """Headless run. Returns a process exit code."""
    try:
        result = ExecutionService().run_file(inputFile, outputFile)
    except (OSError, InputFormatError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for line in result.printedOutput:
        print(line)
    if result.status is RunStatus.SYNTAX_ERROR:
        print(f"syntax error: {result.syntaxError}", file=sys.stderr)
        return 2
    return 0


def run_graphical(inputFile: Path | None, outputFile: Path | None) -> int:
    """Start the PySide6 IDE. PySide6 is imported only here, never in ``-q`` mode."""
    try:
        from robot_ide.ui.app import run_gui
    except ImportError as error:
        print(f"error: PySide6 is required for GUI mode ({error})", file=sys.stderr)
        return 3
    return run_gui(inputFile, outputFile)


def main(argv: Sequence[str] | None = None) -> int:
    """Program entry point."""
    arguments = build_argument_parser().parse_args(argv)
    if arguments.quiet:
        if arguments.inputFile is None or arguments.outputFile is None:
            print("error: -q needs an input and an output file", file=sys.stderr)
            return 2
        return run_quiet(arguments.inputFile, arguments.outputFile)
    return run_graphical(arguments.inputFile, arguments.outputFile)
