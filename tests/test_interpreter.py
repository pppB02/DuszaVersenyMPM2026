from helpers import log_lines, run_program
from robot_ide.core.enums import Direction, RunStatus


def test_while_loop_counts() -> None:
    result = run_program(">", "set i to 0\nwhile i < 3\n  set i to i + 1\nprint i")
    assert result.printedOutput == ["3"]
    assert result.status is RunStatus.COMPLETED


def test_if_else_branches() -> None:
    program = (
        "set a to 1\nif a = 1\n  print 10\nelse\n  print 20\n"
        "if a = 2\n  print 30\nelse\n  print 40"
    )
    assert run_program(">", program).printedOutput == ["10", "40"]


def test_robot_actions_change_central_state() -> None:
    result = run_program(">@.", "step forward 1\nmine here\nturn by 1")
    assert result.simulation is not None
    robot = result.simulation.robot
    assert (robot.x, robot.minedGold, robot.direction) == (1, 1, Direction.NORTH)


def test_runtime_error_stops_execution_and_robot_stays() -> None:
    result = run_program(">.#", "step forward 5\nprint 1")
    assert result.status is RunStatus.RUNTIME_ERROR
    assert result.printedOutput == []
    assert result.simulation is not None and result.simulation.robot.x == 1


def test_empty_program_completes() -> None:
    result = run_program(">", "")
    assert result.status is RunStatus.COMPLETED
    assert log_lines(result) == ["EOR"]


def test_syntax_error_reported_without_running() -> None:
    result = run_program(">", "print 1 +")
    assert result.status is RunStatus.SYNTAX_ERROR
    assert result.syntaxError is not None and result.syntaxError.lineNumber == 1
