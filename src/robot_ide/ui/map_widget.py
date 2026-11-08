"""Maze view: grid, hidden/discovered cells, gold, robot with heading, sensor target."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from robot_ide.core.enums import CellType, Direction
from robot_ide.simulator.sensor import Sensor
from robot_ide.simulator.simulation_state import SimulationState
from robot_ide.ui.styles import LIGHT, MapColors, map_colors

DIRECTION_NAMES = {
    Direction.NORTH: "észak",
    Direction.EAST: "kelet",
    Direction.SOUTH: "dél",
    Direction.WEST: "nyugat",
}


class MapWidget(QWidget):
    """Draws the simulation state. It only reads the model, it never changes it."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._simulation: SimulationState | None = None
        self._colors: MapColors = map_colors(LIGHT)
        self._revealAll = False
        self.setMinimumSize(240, 240)

    def set_simulation(self, simulation: SimulationState) -> None:
        """Show another simulation."""
        self._simulation = simulation
        self.update()

    def set_theme(self, theme: str) -> None:
        """Switch colours."""
        self._colors = map_colors(theme)
        self.update()

    def set_reveal_all(self, revealAll: bool) -> None:
        """Show the content of undiscovered cells too (editing aid)."""
        self._revealAll = revealAll
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802 (Qt API name)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(self._colors.background))
        if self._simulation is None:
            return
        world = self._simulation.world
        size = min(self.width() / world.width, self.height() / world.height)
        offsetX = (self.width() - size * world.width) / 2
        offsetY = (self.height() - size * world.height) / 2
        painter.setPen(QPen(QColor(self._colors.grid), 1))
        for y in range(world.height):
            for x in range(world.width):
                rect = QRectF(offsetX + x * size, offsetY + y * size, size, size)
                self._draw_cell(painter, rect, x, y)
        self._draw_sensor(painter, offsetX, offsetY, size)
        self._draw_robot(painter, offsetX, offsetY, size)

    def _draw_cell(self, painter: QPainter, rect: QRectF, x: int, y: int) -> None:
        assert self._simulation is not None
        world = self._simulation.world
        visible = self._revealAll or world.is_discovered(x, y)
        cell = world.cell_at(x, y)
        gridPen = QPen(QColor(self._colors.grid), 1)
        if not visible:
            painter.setBrush(QColor(self._colors.emptyHidden))
            painter.drawRect(rect)
            painter.setPen(QColor(self._colors.text))
            painter.setFont(QFont("sans-serif", max(6, int(rect.height() / 3))))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "?")
            painter.setPen(gridPen)
            return
        wall = cell is CellType.WALL
        painter.setBrush(QColor(self._colors.wall if wall else self._colors.emptyDiscovered))
        painter.drawRect(rect)
        if cell is CellType.GOLD:
            painter.setBrush(QColor(self._colors.gold))
            margin = rect.width() * 0.25
            painter.drawEllipse(rect.adjusted(margin, margin, -margin, -margin))

    def _draw_sensor(self, painter: QPainter, offsetX: float, offsetY: float, size: float) -> None:
        assert self._simulation is not None
        target = Sensor(self._simulation).front_position()
        if not self._simulation.world.is_inside(*target):
            return
        pen = QPen(QColor(self._colors.sensor), max(2.0, size / 12))
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(offsetX + target[0] * size, offsetY + target[1] * size, size, size))
        painter.setPen(QPen(QColor(self._colors.grid), 1))

    def _draw_robot(self, painter: QPainter, offsetX: float, offsetY: float, size: float) -> None:
        assert self._simulation is not None
        robot = self._simulation.robot
        centerX = offsetX + (robot.x + 0.5) * size
        centerY = offsetY + (robot.y + 0.5) * size
        deltaX, deltaY = robot.direction.delta
        radius = size * 0.36
        tip = QPointF(centerX + deltaX * radius, centerY + deltaY * radius)
        backX = centerX - deltaX * radius * 0.7
        backY = centerY - deltaY * radius * 0.7
        left = QPointF(backX - deltaY * radius * 0.8, backY + deltaX * radius * 0.8)
        right = QPointF(backX + deltaY * radius * 0.8, backY - deltaX * radius * 0.8)
        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.setBrush(QColor(self._colors.robot))
        painter.drawPolygon(QPolygonF([tip, left, right]))
