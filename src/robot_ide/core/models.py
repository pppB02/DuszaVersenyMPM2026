"""Small shared data models and value helpers."""

from dataclasses import dataclass

MineValue = int | bool


def is_integer_value(value: object) -> bool:
    """True for MineScript integers (Python ``bool`` is NOT an integer here)."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_boolean_value(value: object) -> bool:
    """True for MineScript booleans."""
    return isinstance(value, bool)


def format_value(value: MineValue) -> str:
    """Render a value the way ``print`` and the log show it."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


@dataclass(frozen=True)
class ProgramInput:
    """Split input file: raw map lines and raw program lines."""

    mapLines: tuple[str, ...]
    programLines: tuple[str, ...]
