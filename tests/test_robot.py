import pytest

from robot_ide.core.enums import Direction
from robot_ide.core.exceptions import BadArgError, BedrockHitError, NoGoldError
from robot_ide.simulator.map_loader import build_simulation
from robot_ide.simulator.robot import Robot
from robot_ide.simulator.simulation_state import SimulationState


def make_robot(rows: list[str]) -> tuple[Robot, SimulationState]:
    state = build_simulation(len(rows), len(rows[0]), rows)
    return Robot(state), state


@pytest.mark.parametrize(
    ("char", "expected"),
    [(">", (2, 1)), ("<", (0, 1)), ("^", (1, 0)), ("v", (1, 2))],
)
def test_moves_in_four_directions(char: str, expected: tuple[int, int]) -> None:
    robot, state = make_robot(["...", f".{char}.", "..."])
    robot.step_forward(1)
    assert (state.robot.x, state.robot.y) == expected


def test_turn_is_counter_clockwise_modulo_four() -> None:
    robot, state = make_robot([">"])
    expected = [Direction.NORTH, Direction.WEST, Direction.SOUTH, Direction.EAST]
    for direction in expected:
        robot.turn_by(1)
        assert state.robot.direction is direction
    robot.turn_by(5)
    assert state.robot.direction is Direction.NORTH
    robot.turn_by(0)
    assert state.robot.direction is Direction.NORTH


def test_multi_step_discovers_intermediate_cells() -> None:
    robot, state = make_robot([">...."])
    robot.step_forward(3)
    assert state.robot.x == 3
    assert all(state.world.is_discovered(x, 0) for x in (0, 1, 2, 3))
    assert not state.world.is_discovered(4, 0)


def test_stepping_onto_gold_does_not_mine() -> None:
    robot, state = make_robot([">@"])
    robot.step_forward(1)
    assert state.robot.minedGold == 0


def test_wall_stops_robot_on_last_free_cell() -> None:
    robot, state = make_robot([">.#.."])
    with pytest.raises(BedrockHitError):
        robot.step_forward(3)
    assert state.robot.x == 1


def test_map_edge_is_bedrock() -> None:
    robot, state = make_robot([">."])
    with pytest.raises(BedrockHitError):
        robot.step_forward(2)
    assert state.robot.x == 1


def test_negative_arguments_rejected() -> None:
    robot, _ = make_robot([">."])
    with pytest.raises(BadArgError):
        robot.step_forward(-1)
    with pytest.raises(BadArgError):
        robot.turn_by(-1)


def test_mine_gold_once() -> None:
    robot, state = make_robot([">@"])
    robot.step_forward(1)
    robot.mine_here()
    assert state.robot.minedGold == 1
    with pytest.raises(NoGoldError):
        robot.mine_here()


def test_mine_without_gold_fails() -> None:
    robot, _ = make_robot([">."])
    with pytest.raises(NoGoldError):
        robot.mine_here()
