"""Variable storage with first-assignment type locking."""

from robot_ide.core.exceptions import TypeMismatchError, UninitializedError
from robot_ide.core.models import MineValue


class Environment:
    """Maps variable names to values. A variable's type is fixed by its first ``set``."""

    def __init__(self) -> None:
        self._values: dict[str, MineValue] = {}

    def get(self, name: str) -> MineValue:
        """Read a variable or raise ``UninitializedError``."""
        if name not in self._values:
            raise UninitializedError(f"variable {name!r} is not initialized")
        return self._values[name]

    def assign(self, name: str, value: MineValue) -> None:
        """Create a variable or update it with a value of the same type."""
        if name in self._values and type(self._values[name]) is not type(value):
            raise TypeMismatchError(f"variable {name!r} cannot change its type")
        self._values[name] = value

    def snapshot(self) -> dict[str, MineValue]:
        """Copy of all variables (for the variables panel)."""
        return dict(self._values)
