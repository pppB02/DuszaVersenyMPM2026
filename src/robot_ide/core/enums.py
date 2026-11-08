"""Enumerations shared by every layer."""

from enum import Enum


class Direction(Enum):
    """Robot heading. Values are ordered counter-clockwise, so a left turn adds 1."""

    EAST = 0
    NORTH = 1
    WEST = 2
    SOUTH = 3

    def turned_left(self, quarterTurns: int) -> "Direction":
        """Return the heading after turning left by ``quarterTurns`` (modulo 4)."""
        return Direction((self.value + quarterTurns) % 4)

    @property
    def delta(self) -> tuple[int, int]:
        """Return the (dx, dy) of one step; y grows downwards."""
        return _DIRECTION_DELTAS[self]


_DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.EAST: (1, 0),
    Direction.NORTH: (0, -1),
    Direction.WEST: (-1, 0),
    Direction.SOUTH: (0, 1),
}


class CellType(Enum):
    """Content of one map cell."""

    EMPTY = 0
    WALL = 1
    GOLD = 2


class ErrorCode(Enum):
    """Runtime error codes defined by the specification."""

    E_TYPE_MISMATCH = "E_TYPE_MISMATCH"
    E_UNINITIALIZED = "E_UNINITIALIZED"
    E_NON_BOOL_CONDITION = "E_NON_BOOL_CONDITION"
    E_BAD_OPERAND = "E_BAD_OPERAND"
    E_BEDROCK_HIT = "E_BEDROCK_HIT"
    E_NO_GOLD = "E_NO_GOLD"
    E_BAD_ARG = "E_BAD_ARG"


class Operator(Enum):
    """Operators usable in MineScript expressions."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    LESS = "<"
    LESS_EQUAL = "<="
    GREATER = ">"
    GREATER_EQUAL = ">="
    EQUAL = "="
    NOT_EQUAL = "<>"
    AND = "and"
    OR = "or"
    NOT = "not"


class RunStatus(Enum):
    """How a program run ended."""

    COMPLETED = "COMPLETED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    STOPPED = "STOPPED"
