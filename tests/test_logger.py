import tempfile
from pathlib import Path

from helpers import log_lines, run_program
from robot_ide.core.enums import ErrorCode
from robot_ide.logging.execution_logger import ExecutionLogger
from robot_ide.services.execution_service import ExecutionService


def test_logger_format_parts_and_end() -> None:
    logger = ExecutionLogger()
    logger.begin_line(1)
    logger.add_part("isThere")
    logger.add_part("2")
    logger.add_part("false")
    logger.begin_line(2)
    logger.log_end_of_run()
    assert logger.lines == ["1 isThere 2 false", "2", "EOR"]
    assert logger.to_text().endswith("EOR\n")


def test_logger_error_code_closes_without_eor() -> None:
    logger = ExecutionLogger()
    logger.begin_line(8)
    logger.add_part("isThere")
    logger.add_part("3")
    logger.log_error(ErrorCode.E_BAD_ARG)
    assert logger.lines == ["8 isThere 3 E_BAD_ARG"]


def test_specification_style_example() -> None:
    program = (
        "set a to isThere 2\nset b to 1\nturn by 0\nprint a\nset c to 2\nset d to isThere 3"
    )
    result = run_program(">.", program)
    assert log_lines(result) == [
        "1 isThere 2 false",
        "2",
        "3 turn by 0",
        "4 print false",
        "5",
        "6 isThere 3 E_BAD_ARG",
    ]


def test_uninitialized_api_parameter_is_not_printed() -> None:
    assert log_lines(run_program(">.", "set d to isThere q")) == ["1 isThere E_UNINITIALIZED"]


def test_robot_api_lines() -> None:
    result = run_program(">@", "step forward 1\nmine here\nprint 5")
    assert log_lines(result) == ["1 step forward 1", "2 mine here", "3 print 5", "EOR"]


def test_api_error_codes_in_log() -> None:
    assert log_lines(run_program(">#", "step forward 1")) == ["1 step forward 1 E_BEDROCK_HIT"]
    assert log_lines(run_program(">.", "mine here")) == ["1 mine here E_NO_GOLD"]
    assert log_lines(run_program(">.", "set a to 1\nset a to true")) == ["1", "2 E_TYPE_MISMATCH"]
    assert log_lines(run_program(">.", "if 1\n  print 1")) == ["1 E_NON_BOOL_CONDITION"]


def test_else_logged_only_when_taken() -> None:
    program = "if {c}\n  print 1\nelse\n  print 2"
    assert log_lines(run_program(">", program.format(c="false"))) == ["1", "3", "4 print 2", "EOR"]
    assert log_lines(run_program(">", program.format(c="true"))) == ["1", "2 print 1", "EOR"]


def test_while_condition_logged_every_check() -> None:
    program = "set i to 0\nwhile i < 2\n  set i to i + 1"
    assert log_lines(run_program(">", program)) == ["1", "2", "3", "2", "3", "2", "EOR"]


def test_instruction_limit() -> None:
    lines = log_lines(run_program(">", "while true\n  set a to 1"))
    assert len(lines) == 1001
    assert lines[:3] == ["1", "2", "1"]
    assert lines[999] == "2"
    assert lines[-1] == "INSTRUCTION_COUNT_LIMIT_EXCEEDED"
    assert "EOR" not in lines


def test_exactly_limit_lines_completes_with_eor() -> None:
    inputText = "1 1\n>\nset a to 1\nset b to 2\nset c to 3"
    result = ExecutionService(maxExecutedLines=3).run_text(inputText)
    assert log_lines(result) == ["1", "2", "3", "EOR"]


def test_no_trailing_spaces() -> None:
    result = run_program(">@", "step forward 1\nmine here\nprint 5")
    assert all(line == line.strip() and "  " not in line for line in log_lines(result))


def test_output_file_is_overwritten_each_run() -> None:
    with tempfile.TemporaryDirectory() as directory:
        inputPath = Path(directory) / "in.txt"
        outputPath = Path(directory) / "out.txt"
        outputPath.write_text("OLD CONTENT\n", encoding="utf-8")
        inputPath.write_text("1 1\n>\nprint 1\n", encoding="utf-8")
        ExecutionService().run_file(inputPath, outputPath)
        ExecutionService().run_file(inputPath, outputPath)
        assert outputPath.read_text(encoding="utf-8") == "1 print 1\nEOR\n"
