from robot_ide.core.enums import CellType, Direction, RunStatus
from robot_ide.services.debug_session import DebugSession
from robot_ide.services.manual_control import (
    MESSAGE_NO_GOLD,
    MESSAGE_WALL_AHEAD,
    ManualControlService,
)
from robot_ide.simulator.map_loader import build_simulation
from robot_ide.simulator.sensor import Sensor


def make(rows: list[str]) -> tuple[DebugSession, ManualControlService]:
    session = DebugSession(build_simulation(len(rows), len(rows[0]), rows))
    return session, ManualControlService(session)


def test_forward_one_cell() -> None:
    session, manual = make([">.."])
    result = manual.step_forward()
    assert result.succeeded
    assert session.simulation.robot.x == 1


def test_turn_left_ninety_degrees_keeps_position() -> None:
    session, manual = make(["...", ".>.", "..."])
    manual.turn_left()
    robot = session.simulation.robot
    assert robot.direction is Direction.NORTH
    assert (robot.x, robot.y) == (1, 1)


def test_multiple_quarter_turns_and_zero() -> None:
    session, manual = make([">"])
    manual.turn_left(3)
    assert session.simulation.robot.direction is Direction.SOUTH
    manual.turn_left(0)
    assert session.simulation.robot.direction is Direction.SOUTH
    manual.turn_left(5)
    assert session.simulation.robot.direction is Direction.EAST


def test_negative_turn_is_refused_without_change() -> None:
    session, manual = make([">"])
    result = manual.turn_left(-1)
    assert not result.succeeded
    assert session.simulation.robot.direction is Direction.EAST


def test_wall_ahead_no_move_no_error_no_discovery() -> None:
    session, manual = make([">#"])
    result = manual.step_forward()
    assert not result.succeeded and result.message == MESSAGE_WALL_AHEAD
    assert session.simulation.robot.x == 0
    assert not session.simulation.world.is_discovered(1, 0)
    assert session.logText == ""


def test_map_edge_does_not_leave_the_map() -> None:
    session, manual = make([">"])
    assert not manual.step_forward().succeeded
    assert (session.simulation.robot.x, session.simulation.robot.y) == (0, 0)
    manual.turn_left()
    assert not manual.step_forward().succeeded
    assert session.simulation.robot.y == 0


def test_mine_gold_and_counter() -> None:
    session, manual = make([">@"])
    manual.step_forward()
    assert manual.mine_here().succeeded
    assert session.simulation.robot.minedGold == 1
    assert session.simulation.world.cell_at(1, 0) is CellType.EMPTY


def test_cannot_mine_twice_on_same_cell() -> None:
    session, manual = make([">@"])
    manual.step_forward()
    manual.mine_here()
    result = manual.mine_here()
    assert not result.succeeded and result.message == MESSAGE_NO_GOLD
    assert session.simulation.robot.minedGold == 1


def test_mine_without_gold_changes_nothing() -> None:
    session, manual = make([">."])
    assert not manual.mine_here().succeeded
    assert session.simulation.robot.minedGold == 0


def test_sensor_after_move() -> None:
    session, manual = make([">.@#"])
    sensor = Sensor(session.simulation)
    assert sensor.peek() is CellType.EMPTY
    manual.step_forward()
    assert sensor.peek() is CellType.GOLD
    manual.step_forward()
    assert sensor.peek() is CellType.WALL


def test_sensor_after_turn_and_map_edge() -> None:
    session, manual = make(["#.", ">@"])
    sensor = Sensor(session.simulation)
    assert sensor.peek() is CellType.GOLD
    manual.turn_left()
    assert sensor.peek() is CellType.WALL  # cell above is a wall
    manual.turn_left()
    assert sensor.peek() is CellType.WALL  # map edge on the west
    manual.turn_left()
    assert sensor.peek() is CellType.WALL  # map edge on the south


def test_sensor_display_does_not_discover() -> None:
    session, manual = make([">@."])
    sensor = Sensor(session.simulation)
    sensor.peek()
    manual.turn_left(4)
    sensor.peek()
    assert not session.simulation.world.is_discovered(1, 0)
    assert session.simulation.robot.sensorResult is None


def test_new_cell_becomes_discovered_old_stay_discovered() -> None:
    session, manual = make([">..."])
    manual.step_forward()
    manual.turn_left()
    manual.step_forward()  # wall (map edge) - nothing changes
    world = session.simulation.world
    assert world.is_discovered(0, 0) and world.is_discovered(1, 0)
    assert not world.is_discovered(2, 0)


def test_manual_action_stops_active_run() -> None:
    session, manual = make([">..."])
    session.start("while true\n  set a to 1")
    session.step()
    assert session.is_active
    manual.step_forward()
    assert not session.is_active
    assert session.status is RunStatus.STOPPED


def test_state_is_kept_when_switching_from_running_program() -> None:
    session, manual = make([">@.."])
    session.start("step forward 1\nmine here\nstep forward 1\nstep forward 1")
    session.step()
    session.step()  # step forward 1 and mine here ran
    robot = session.simulation.robot
    assert (robot.x, robot.minedGold) == (1, 1)
    manual.turn_left(0)
    assert (robot.x, robot.minedGold) == (1, 1)
    assert session.simulation.world.is_discovered(1, 0)
    manual.step_forward()
    assert (session.simulation.robot.x, session.simulation.robot.minedGold) == (2, 1)


def test_manual_actions_do_not_touch_program_log() -> None:
    session, manual = make([">@."])
    session.start("step forward 1\nprint 1")
    session.step()
    logBefore = session.logText
    manual.step_forward()
    manual.turn_left()
    manual.mine_here()
    assert session.logText == logBefore
    assert "EOR" not in session.logText


def test_no_parallel_modification_after_takeover() -> None:
    session, manual = make([">..."])
    session.start("step forward 3")
    manual.step_forward()
    assert session.step() is False  # the stopped run cannot move the robot any more
    assert session.simulation.robot.x == 1


def test_manual_does_not_reset_simulation() -> None:
    session, manual = make([">@."])
    manual.step_forward()
    manual.mine_here()
    manual.turn_left()
    assert session.simulation.robot.minedGold == 1
    assert session.simulation.robot.x == 1


def test_program_run_still_resets_and_keeps_api_rules() -> None:
    session, manual = make([">@#"])
    manual.step_forward()
    manual.mine_here()
    session.start("step forward 5")
    assert session.simulation.robot.x == 0 and session.simulation.robot.minedGold == 0
    while session.step():
        pass
    assert session.status is RunStatus.RUNTIME_ERROR
    assert session.runtimeError is not None
    assert session.runtimeError.errorCode.value == "E_BEDROCK_HIT"
    assert session.logText.splitlines() == ["1 step forward 5 E_BEDROCK_HIT"]
