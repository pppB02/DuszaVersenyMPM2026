"""Read-only MineScript text with line numbers and current-line highlight."""

from PySide6.QtGui import QColor, QTextCursor, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget


class SourceCodeWidget(QPlainTextEdit):
    """Shows generated code. It cannot be edited: the block editor is the only editor."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._highlightColor = QColor("#fde68a")
        self._lineCount = 0

    def set_highlight_color(self, color: str) -> None:
        """Colour of the current-line highlight."""
        self._highlightColor = QColor(color)

    def show_code(self, lines: list[str]) -> None:
        """Replace the text (line numbers are added for display only)."""
        self._lineCount = len(lines)
        numbered = (f"{number:>3}  {line}" for number, line in enumerate(lines, 1))
        self.setPlainText("\n".join(numbered))
        self.highlight_line(None)

    def highlight_line(self, lineNumber: int | None) -> None:
        """Mark the line that executes next (1-based), or clear the mark."""
        if lineNumber is None or not 1 <= lineNumber <= self._lineCount:
            self.setExtraSelections([])
            return
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(self._highlightColor)
        selection.format.setForeground(QColor("#000000"))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(
            QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, lineNumber - 1
        )
        selection.cursor = cursor
        self.setExtraSelections([selection])
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
