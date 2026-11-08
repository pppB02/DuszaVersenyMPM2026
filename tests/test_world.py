import pytest

from robot_ide.core.enums import CellType, Direction
from robot_ide.core.exceptions import InputFormatError
from robot_ide.simulator.map_loader import build_simulation, parse_map_size


def test_map_loads_cells_robot_and_direction() -> None:
    state = build_simulation(2, 3, ["#.@", "v.."])
    assert state.world.cell_at(0, 0) is CellType.WALL
    assert state.world.cell_at(2, 0) is CellType.GOLD
    assert (state.robot.x, state.robot.y) == (0, 1)
    assert state.robot.direction is Direction.SOUTH
    assert state.world.cell_at(0, 1) is CellType.EMPTY


def test_robot_start_is_discovered_others_not() -> None:
    state = build_simulation(1, 3, [">.."])
    assert state.world.is_discovered(0, 0)
    assert not state.world.is_discovered(1, 0)


def test_off_map_reads_as_wall() -> None:
    state = build_simulation(1, 1, [">"])
    assert state.world.cell_at(-1, 0) is CellType.WALL
    assert state.world.cell_at(0, 5) is CellType.WALL


@pytest.mark.parametrize("line", ["0 5", "16 3", "3 16", "3", "a b", "1 2 3", ""])
def test_bad_size_line_rejected(line: str) -> None:
    with pytest.raises(InputFormatError):
        parse_map_size(line)


def test_size_bounds_accepted() -> None:
    assert parse_map_size("1 1") == (1, 1)
    assert parse_map_size("15 15") == (15, 15)


@pytest.mark.parametrize(
    "rows",
    [
        ["..."],  # no robot
        [">.>"],  # two robots
        [">.", "..."],  # ragged row
        [">x."],  # unknown char
    ],
)
def test_bad_maps_rejected(rows: list[str]) -> None:
    with pytest.raises(InputFormatError):
        build_simulation(len(rows), 3, rows)


def test_wrong_row_count_rejected() -> None:
    with pytest.raises(InputFormatError):
        build_simulation(2, 3, [">.."])


def test_reset_restores_everything() -> None:
    state = build_simulation(1, 3, [">@."])
    state.robot.x = 1
    state.robot.minedGold = 1
    state.world.clear_gold(1, 0)
    state.world.mark_discovered(2, 0)
    state.reset()
    assert (state.robot.x, state.robot.minedGold) == (0, 0)
    assert state.world.cell_at(1, 0) is CellType.GOLD
    assert not state.world.is_discovered(2, 0)
