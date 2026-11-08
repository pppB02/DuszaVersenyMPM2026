"""Status strip under the map: position, heading, gold, sensor, run state."""

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from robot_ide.simulator.simulation_state import SimulationState
from robot_ide.ui.map_widget import DIRECTION_NAMES


class RobotStatusWidget(QWidget):
    """Read-only robot information."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        self._labels: dict[str, QLabel] = {}
        titles = [
            ("position", "Pozíció"),
            ("direction", "Irány"),
            ("gold", "Arany"),
            ("sensor", "Érzékelő"),
            ("state", "Állapot"),
        ]
        for column, (key, title) in enumerate(titles):
            layout.addWidget(QLabel(f"<b>{title}</b>"), 0, column)
            valueLabel = QLabel("-")
            self._labels[key] = valueLabel
            layout.addWidget(valueLabel, 1, column)

    def update_from(self, simulation: SimulationState, runState: str) -> None:
        """Refresh all fields from the central model."""
        robot = simulation.robot
        sensor = "-" if robot.sensorResult is None else ("igaz" if robot.sensorResult else "hamis")
        self._labels["position"].setText(f"({robot.x}, {robot.y})")
        self._labels["direction"].setText(DIRECTION_NAMES[robot.direction])
        self._labels["gold"].setText(str(robot.minedGold))
        self._labels["sensor"].setText(sensor)
        self._labels["state"].setText(runState)
