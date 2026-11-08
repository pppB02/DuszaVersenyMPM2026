"""Run log in the competition format: one line per executed program line."""

from pathlib import Path

from robot_ide.core.constants import END_OF_RUN_MARKER, LIMIT_EXCEEDED_MARKER
from robot_ide.core.enums import ErrorCode


class ExecutionLogger:
    """Collects log lines.

    A line starts with its source line number. Parts (API name, parameter, return value,
    error code) are appended, separated by exactly one space.
    """

    def __init__(self) -> None:
        self._entries: list[str] = []
        self._pendingParts: list[str] | None = None

    def reset(self) -> None:
        """Discard everything (start of a new run)."""
        self._entries = []
        self._pendingParts = None

    def begin_line(self, lineNumber: int) -> None:
        """Start the entry of a newly executed program line."""
        self._flush_pending()
        self._pendingParts = [str(lineNumber)]

    def add_part(self, text: str) -> None:
        """Append a part to the current line entry."""
        if self._pendingParts is None:
            raise RuntimeError("add_part called before begin_line")
        self._pendingParts.append(text)

    def log_error(self, errorCode: ErrorCode) -> None:
        """Append the error code to the current line and close the log (no EOR)."""
        self.add_part(errorCode.value)
        self._flush_pending()

    def log_end_of_run(self) -> None:
        """Close the log after a normal finish."""
        self._flush_pending()
        self._entries.append(END_OF_RUN_MARKER)

    def log_limit_exceeded(self) -> None:
        """Close the log because the instruction limit was hit (no EOR)."""
        self._flush_pending()
        self._entries.append(LIMIT_EXCEEDED_MARKER)

    @property
    def lines(self) -> list[str]:
        """Log lines so far; a still-open line entry is shown but stays open."""
        if self._pendingParts is None:
            return list(self._entries)
        return [*self._entries, " ".join(self._pendingParts)]

    def to_text(self) -> str:
        """Whole log as text, newline-terminated; empty string if nothing was logged."""
        lines = self.lines
        return "\n".join(lines) + "\n" if lines else ""

    def write_to_file(self, path: Path) -> None:
        """Write the log, overwriting any existing file."""
        path.write_text(self.to_text(), encoding="utf-8")

    def _flush_pending(self) -> None:
        if self._pendingParts is not None:
            self._entries.append(" ".join(self._pendingParts))
            self._pendingParts = None
