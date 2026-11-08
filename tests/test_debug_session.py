from robot_ide.core.enums import RunStatus
from robot_ide.services.debug_session import DebugSession
from robot_ide.simulator.map_loader import build_simulation


def make_session(mapText: str = ">@.") -> DebugSession:
    rows = mapText.splitlines()
    return DebugSession(build_simulation(len(rows), len(rows[0]), rows))


def test_start_stops_at_first_line_without_executing() -> None:
    session = make_session()
    session.start("set a to 1\nstep forward 1")
    assert session.currentLine == 1
    assert session.variables == {}
    assert session.executedLines == 0
    assert session.is_active


def test_each_step_runs_one_line() -> None:
    session = make_session()
    session.start("set a to 1\nstep forward 1\nmine here")
    assert session.step() and session.currentLine == 2
    assert session.variables == {"a": 1}
    assert session.executedLines == 1
    session.step()
    assert session.simulation.robot.x == 1
    assert session.currentLine == 3
    assert session.step() is False
    assert session.status is RunStatus.COMPLETED
    assert session.currentLine is None
    assert session.executedLines == 3
    assert session.logText.splitlines()[-1] == "EOR"


def test_loop_lines_are_visited_each_time() -> None:
    session = make_session()
    session.start("set i to 0\nwhile i < 2\n  set i to i + 1")
    visited = [session.currentLine]
    while session.step():
        visited.append(session.currentLine)
    assert visited == [1, 2, 3, 2, 3, 2]


def test_print_output_and_variable_types() -> None:
    session = make_session()
    session.start("set a to true\nset b to 4\nprint b")
    while session.step():
        pass
    assert session.printedOutput == ["4"]
    assert session.variables == {"a": True, "b": 4}


def test_runtime_error_ends_run_with_line() -> None:
    session = make_session()
    session.start("print 1\nmine here\nprint 2")
    while session.step():
        pass
    assert session.status is RunStatus.RUNTIME_ERROR
    assert session.runtimeError is not None and session.runtimeError.lineNumber == 2
    assert session.printedOutput == ["1"]
    assert session.logText.splitlines() == ["1 print 1", "2 mine here E_NO_GOLD"]


def test_partial_log_is_readable_and_stays_consistent_mid_run() -> None:
    session = make_session()
    session.start("step forward 1\nmine here")
    assert session.logText == "1\n"
    session.step()
    assert session.logText.splitlines() == ["1 step forward 1", "2"]
    session.step()
    assert session.logText.splitlines() == ["1 step forward 1", "2 mine here", "EOR"]


def test_stop_aborts_without_eor() -> None:
    session = make_session()
    session.start("while true\n  set a to 1")
    session.step()
    session.stop()
    assert session.status is RunStatus.STOPPED and not session.is_active
    assert "EOR" not in session.logText


def test_restart_resets_simulation_and_state() -> None:
    session = make_session()
    program = "step forward 1\nmine here\nprint 9"
    session.start(program)
    while session.step():
        pass
    assert session.simulation.robot.minedGold == 1
    session.start(program)
    robot = session.simulation.robot
    assert (robot.x, robot.minedGold) == (0, 0)
    assert session.printedOutput == [] and session.variables == {}
    assert session.simulation.world.cell_at(1, 0).name == "GOLD"


def test_syntax_error_is_reported_and_nothing_runs() -> None:
    session = make_session()
    session.start("print 1 +")
    assert session.status is RunStatus.SYNTAX_ERROR
    assert session.syntaxError is not None and not session.is_active
    assert session.step() is False


def test_empty_program_finishes_immediately() -> None:
    session = make_session()
    session.start("")
    assert session.status is RunStatus.COMPLETED and session.logText == "EOR\n"


def test_instruction_limit_through_session() -> None:
    session = make_session()
    session.start("while true\n  set a to 1")
    count = 0
    while session.step():
        count += 1
    assert session.status is RunStatus.LIMIT_EXCEEDED
    assert session.logText.splitlines()[-1] == "INSTRUCTION_COUNT_LIMIT_EXCEEDED"
    assert session.executedLines == 1000
    assert count == 999
