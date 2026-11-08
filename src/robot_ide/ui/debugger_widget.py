"""Debugger info panel: current line, executed count, robot state."""

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from robot_ide.simulator.simulation_state import SimulationState
from robot_ide.ui.map_widget import DIRECTION_NAMES


class DebuggerWidget(QWidget):
    """Shows where the run is and what the robot looks like."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self._line = QLabel("-")
        self._count = QLabel("0")
        self._robot = QLabel("-")
        self._state = QLabel("Készenlét")
        layout.addRow("Aktuális sor:", self._line)
        layout.addRow("Végrehajtott utasítások:", self._count)
        layout.addRow("Robot:", self._robot)
        layout.addRow("Állapot:", self._state)

    def update_info(
        self, currentLine: int | None, executed: int, simulation: SimulationState, state: str
    ) -> None:
        """Refresh the panel."""
        robot = simulation.robot
        self._line.setText("-" if currentLine is None else str(currentLine))
        self._count.setText(str(executed))
        direction = DIRECTION_NAMES[robot.direction]
        self._robot.setText(f"({robot.x}, {robot.y}) {direction}, arany: {robot.minedGold}")
        self._state.setText(state)
