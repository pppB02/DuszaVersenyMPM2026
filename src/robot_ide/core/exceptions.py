"""Exception classes. Runtime errors carry code, source line and description."""

from robot_ide.core.enums import ErrorCode


class MineScriptError(Exception):
    """Base class of all MineScript errors."""


class InputFormatError(Exception):
    """The input file (map header, map body) is malformed."""


class MineScriptSyntaxError(MineScriptError):
    """The program text cannot be parsed."""

    def __init__(self, lineNumber: int, description: str) -> None:
        super().__init__(f"line {lineNumber}: {description}")
        self.lineNumber = lineNumber
        self.description = description


class BlockEditError(Exception):
    """A block edit is not allowed (bad name, nesting limit, wrong target, ...)."""


class InstructionLimitExceededError(MineScriptError):
    """More program lines would run than the central limit allows."""


class MineRuntimeError(MineScriptError):
    """Runtime error with a specification error code."""

    errorCode: ErrorCode

    def __init__(self, description: str, lineNumber: int = 0) -> None:
        super().__init__(f"{self.errorCode.value} (line {lineNumber}): {description}")
        self.description = description
        self.lineNumber = lineNumber

    def attach_line(self, lineNumber: int) -> None:
        """Set the source line if the raiser did not know it."""
        if self.lineNumber == 0:
            self.lineNumber = lineNumber


class TypeMismatchError(MineRuntimeError):
    """A variable would change its type."""

    errorCode = ErrorCode.E_TYPE_MISMATCH


class UninitializedError(MineRuntimeError):
    """A variable is read before its first ``set``."""

    errorCode = ErrorCode.E_UNINITIALIZED


class NonBoolConditionError(MineRuntimeError):
    """An ``if`` or ``while`` condition is not boolean."""

    errorCode = ErrorCode.E_NON_BOOL_CONDITION


class BadOperandError(MineRuntimeError):
    """An operator got operands of the wrong type."""

    errorCode = ErrorCode.E_BAD_OPERAND


class BedrockHitError(MineRuntimeError):
    """The robot hit a wall or the map edge."""

    errorCode = ErrorCode.E_BEDROCK_HIT


class NoGoldError(MineRuntimeError):
    """The robot tried to mine a cell without gold."""

    errorCode = ErrorCode.E_NO_GOLD


class BadArgError(MineRuntimeError):
    """A robot API call got an invalid argument."""

    errorCode = ErrorCode.E_BAD_ARG
