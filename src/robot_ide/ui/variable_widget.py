"""Variables table: name, type, value."""

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from robot_ide.core.models import MineValue, format_value


class VariableWidget(QTableWidget):
    """Shows the current variable values."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels(["Név", "Típus", "Érték"])
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def show_variables(self, variables: dict[str, MineValue]) -> None:
        """Replace the table content."""
        self.setRowCount(len(variables))
        for row, (name, value) in enumerate(variables.items()):
            typeName = "boolean" if isinstance(value, bool) else "integer"
            for column, text in enumerate((name, typeName, format_value(value))):
                self.setItem(row, column, QTableWidgetItem(text))
