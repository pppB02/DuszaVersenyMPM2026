"""Input file handling: read text, split map from program, build the simulation."""

from pathlib import Path

from robot_ide.core.exceptions import InputFormatError
from robot_ide.core.models import ProgramInput
from robot_ide.simulator.map_loader import build_simulation, parse_map_size
from robot_ide.simulator.simulation_state import SimulationState


def read_text(path: Path) -> str:
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


def split_input(text: str) -> tuple[tuple[int, int], ProgramInput]:
    """Split input text into map size, map rows and program lines."""
    lines = text.splitlines()
    if not lines:
        raise InputFormatError("input file is empty")
    rowCount, columnCount = parse_map_size(lines[0])
    mapLines = tuple(lines[1 : 1 + rowCount])
    programLines = tuple(lines[1 + rowCount :])
    return (rowCount, columnCount), ProgramInput(mapLines, programLines)


def load_input(text: str) -> tuple[SimulationState, ProgramInput]:
    """Parse input text into a simulation state and the raw program lines."""
    (rowCount, columnCount), programInput = split_input(text)
    simulation = build_simulation(rowCount, columnCount, programInput.mapLines)
    return simulation, programInput


def write_text(path: Path, text: str) -> None:
    """Write a UTF-8 text file."""
    path.write_text(text, encoding="utf-8")
