"""Map text -> :class:`SimulationState`."""

from collections.abc import Sequence

from robot_ide.core.constants import (
    CHAR_EMPTY,
    CHAR_GOLD,
    CHAR_WALL,
    MAX_MAP_SIZE,
    MIN_MAP_SIZE,
)
from robot_ide.core.enums import CellType, Direction
from robot_ide.core.exceptions import InputFormatError
from robot_ide.simulator.simulation_state import RobotState, SimulationState
from robot_ide.simulator.world import World

_ROBOT_DIRECTIONS = {
    ">": Direction.EAST,
    "<": Direction.WEST,
    "^": Direction.NORTH,
    "v": Direction.SOUTH,
}
_CELL_CHARS = {CHAR_EMPTY: CellType.EMPTY, CHAR_GOLD: CellType.GOLD, CHAR_WALL: CellType.WALL}


def parse_map_size(sizeLine: str) -> tuple[int, int]:
    """Parse the ``rows columns`` header line."""
    parts = sizeLine.split()
    if len(parts) != 2 or not all(part.isascii() and part.isdigit() for part in parts):
        raise InputFormatError(f"map size line must be 'rows columns': {sizeLine!r}")
    rowCount, columnCount = int(parts[0]), int(parts[1])
    for value in (rowCount, columnCount):
        if not MIN_MAP_SIZE <= value <= MAX_MAP_SIZE:
            raise InputFormatError(f"map size must be {MIN_MAP_SIZE}..{MAX_MAP_SIZE}: {value}")
    return rowCount, columnCount


def format_map(simulation: SimulationState) -> list[str]:
    """Map rows of the INITIAL state, in input-file format."""
    world, robot = simulation.initial_snapshot()
    charByCell = {CellType.EMPTY: CHAR_EMPTY, CellType.GOLD: CHAR_GOLD, CellType.WALL: CHAR_WALL}
    robotChars = {direction: char for char, direction in _ROBOT_DIRECTIONS.items()}
    rows: list[str] = []
    for y in range(world.height):
        chars = [charByCell[cell] for cell in world.cells[y]]
        if y == robot.y:
            chars[robot.x] = robotChars[robot.direction]
        rows.append("".join(chars))
    return rows


def build_simulation(rowCount: int, columnCount: int, mapLines: Sequence[str]) -> SimulationState:
    """Build the simulation state from map rows; exactly one robot is required."""
    if len(mapLines) != rowCount:
        raise InputFormatError(f"expected {rowCount} map rows, got {len(mapLines)}")
    cells: list[list[CellType]] = []
    robot: RobotState | None = None
    for rowIndex, rawLine in enumerate(mapLines):
        line = rawLine.rstrip()
        if len(line) != columnCount:
            raise InputFormatError(
                f"map row {rowIndex + 1} must have {columnCount} characters, got {len(line)}"
            )
        row: list[CellType] = []
        for columnIndex, char in enumerate(line):
            if char in _ROBOT_DIRECTIONS:
                if robot is not None:
                    raise InputFormatError("map must contain exactly one robot")
                robot = RobotState(columnIndex, rowIndex, _ROBOT_DIRECTIONS[char])
                row.append(CellType.EMPTY)
            elif char in _CELL_CHARS:
                row.append(_CELL_CHARS[char])
            else:
                raise InputFormatError(
                    f"unknown map character {char!r} at row {rowIndex + 1}, "
                    f"column {columnIndex + 1}"
                )
        cells.append(row)
    if robot is None:
        raise InputFormatError("map must contain exactly one robot")
    world = World(columnCount, rowCount, cells)
    world.mark_discovered(robot.x, robot.y)
    return SimulationState(world, robot)
