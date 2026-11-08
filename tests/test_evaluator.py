import pytest

from helpers import log_lines, run_program
from robot_ide.core.enums import RunStatus

MAP = ">...."


def printed(program: str) -> list[str]:
    result = run_program(MAP, program)
    assert result.status is RunStatus.COMPLETED, log_lines(result)
    return result.printedOutput


def error_of(program: str) -> str:
    result = run_program(MAP, program)
    assert result.status is RunStatus.RUNTIME_ERROR
    assert result.runtimeError is not None
    return result.runtimeError.errorCode.value


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("3 + 4", "7"),
        ("9 - 4", "5"),
        ("6 * 7", "42"),
        ("2 - 5", "-3"),
        ("1 < 2", "true"),
        ("2 < 2", "false"),
        ("2 <= 2", "true"),
        ("3 > 2", "true"),
        ("2 >= 3", "false"),
        ("4 = 4", "true"),
        ("4 <> 4", "false"),
        ("true = true", "true"),
        ("true <> false", "true"),
        ("true and false", "false"),
        ("true and true", "true"),
        ("false or true", "true"),
        ("false or false", "false"),
        ("not true", "false"),
        ("not false", "true"),
    ],
)
def test_expression_results(expression: str, expected: str) -> None:
    assert printed(f"set r to {expression}\nprint r") == [expected]


def test_variable_operands() -> None:
    assert printed("set a to 3\nset b to a * a\nprint b") == ["9"]


@pytest.mark.parametrize(
    "expression",
    [
        "1 + true", "true * 2", "true < false", "1 and 2",
        "true or 1", "not 1", "1 = true", "true <> 1",
    ],
)
def test_bad_operands(expression: str) -> None:
    assert error_of(f"set r to {expression}") == "E_BAD_OPERAND"


def test_uninitialized_variable() -> None:
    assert error_of("print missing") == "E_UNINITIALIZED"
    assert error_of("set a to missing + 1") == "E_UNINITIALIZED"


def test_no_short_circuit_on_and_or() -> None:
    assert error_of("set a to false and missing") == "E_UNINITIALIZED"
    assert error_of("set a to true or missing") == "E_UNINITIALIZED"
    assert error_of("set a to false and 1") == "E_BAD_OPERAND"


def test_type_is_locked_at_first_assignment() -> None:
    assert error_of("set a to 1\nset a to true") == "E_TYPE_MISMATCH"
    assert error_of("set a to false\nset a to 0") == "E_TYPE_MISMATCH"
    assert printed("set a to 1\nset a to 2\nprint a") == ["2"]


def test_non_boolean_conditions() -> None:
    assert error_of("if 1\n  print 1") == "E_NON_BOOL_CONDITION"
    assert error_of("set a to 3\nwhile a\n  print 1") == "E_NON_BOOL_CONDITION"


def test_error_reports_source_line() -> None:
    result = run_program(MAP, "set a to 1\n\nprint b")
    assert result.runtimeError is not None
    assert result.runtimeError.lineNumber == 3


@pytest.mark.parametrize(
    "program",
    [
        "set b to isThere 3",
        "set a to 0 - 1\nset b to isThere a",
        "set a to true\nset b to isThere a",
        "set a to 100\nset b to isThere a",
    ],
)
def test_is_there_bad_argument(program: str) -> None:
    assert error_of(program) == "E_BAD_ARG"


def test_api_bad_argument_types() -> None:
    assert error_of("step forward true") == "E_BAD_ARG"
    assert error_of("turn by false") == "E_BAD_ARG"
    assert error_of("set a to 0 - 1\nstep forward a") == "E_BAD_ARG"
