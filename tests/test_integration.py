import tempfile
from pathlib import Path

from helpers import log_lines
from robot_ide.cli.command_line import main
from robot_ide.core.enums import RunStatus
from robot_ide.services.execution_service import ExecutionService

PROGRAM = """set count to 0
set megy to true
while megy
  set arany to isThere 2
  if arany
    step forward 1
    mine here
    set count to count + 1
  else
    step forward 1
  set fal to isThere 1
  set megy to not fal
print count"""

INPUT_TEXT = "1 8\n>.@.@..#\n" + PROGRAM

STEP_EMPTY = ["3", "4 isThere 2 false", "5", "9", "10 step forward 1", "11 isThere 1 false", "12"]
STEP_GOLD = [
    "3", "4 isThere 2 true", "5", "6 step forward 1", "7 mine here", "8",
    "11 isThere 1 false", "12",
]
STEP_LAST = STEP_EMPTY[:5] + ["11 isThere 1 true", "12"]


def test_mandatory_example_program() -> None:
    result = ExecutionService().run_text(INPUT_TEXT)
    assert result.status is RunStatus.COMPLETED
    assert result.printedOutput == ["2"]
    expected = ["1", "2"]
    expected += STEP_EMPTY + STEP_GOLD + STEP_EMPTY + STEP_GOLD + STEP_EMPTY + STEP_LAST
    expected += ["3", "13 print 2", "EOR"]
    assert log_lines(result) == expected
    assert result.simulation is not None
    robot = result.simulation.robot
    assert (robot.x, robot.minedGold) == (6, 2)
    assert result.simulation.world.is_discovered(7, 0)


def test_input_file_to_log_file_via_cli() -> None:
    with tempfile.TemporaryDirectory() as directory:
        inputPath = Path(directory) / "input_001.txt"
        outputPath = Path(directory) / "output_001.txt"
        inputPath.write_text(INPUT_TEXT, encoding="utf-8")
        assert main(["-q", str(inputPath), str(outputPath)]) == 0
        lines = outputPath.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "1" and lines[-2:] == ["13 print 2", "EOR"]


def test_bad_input_file_gives_error_exit_code() -> None:
    with tempfile.TemporaryDirectory() as directory:
        inputPath = Path(directory) / "bad.txt"
        outputPath = Path(directory) / "out.txt"
        inputPath.write_text("1 3\n...\n", encoding="utf-8")  # no robot
        assert main(["-q", str(inputPath), str(outputPath)]) == 2
        assert main(["-q", str(Path(directory) / "missing.txt"), str(outputPath)]) == 2


def test_quiet_mode_never_imports_pyside6() -> None:
    import sys

    with tempfile.TemporaryDirectory() as directory:
        inputPath = Path(directory) / "in.txt"
        inputPath.write_text("1 1\n>\nprint 1\n", encoding="utf-8")
        assert main(["-q", str(inputPath), str(Path(directory) / "out.txt")]) == 0
    assert "PySide6" not in sys.modules
    assert "robot_ide.ui" not in sys.modules


def test_quiet_mode_requires_both_files() -> None:
    assert main(["-q"]) == 2
