"""Bottom panel: console (print), run log, errors."""

from PySide6.QtWidgets import QPlainTextEdit, QTabWidget, QWidget


class ConsoleWidget(QTabWidget):
    """Three read-only text tabs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._console = self._add_tab("Konzol")
        self._log = self._add_tab("Programnapló")
        self._errors = self._add_tab("Hibák")

    def _add_tab(self, title: str) -> QPlainTextEdit:
        edit = QPlainTextEdit()
        edit.setReadOnly(True)
        self.addTab(edit, title)
        return edit

    def show_output(self, lines: list[str]) -> None:
        """Replace console text with the printed lines."""
        self._console.setPlainText("\n".join(lines))

    def show_log(self, logText: str) -> None:
        """Replace the run log."""
        self._log.setPlainText(logText)

    def show_errors(self, messages: list[str]) -> None:
        """Replace the error list; switch to the tab if there are errors."""
        self._errors.setPlainText("\n".join(messages))
        if messages:
            self.setCurrentWidget(self._errors)

    def clear_all(self) -> None:
        """Empty every tab (new run)."""
        self._console.clear()
        self._log.clear()
        self._errors.clear()
