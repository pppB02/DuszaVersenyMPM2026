"""Front sensor (``isThere``)."""

from robot_ide.core.constants import SENSOR_EMPTY, SENSOR_GOLD, SENSOR_WALL
from robot_ide.core.enums import CellType
from robot_ide.core.exceptions import BadArgError
from robot_ide.simulator.simulation_state import SimulationState

_SENSOR_CELL_TYPES = {
    SENSOR_EMPTY: CellType.EMPTY,
    SENSOR_WALL: CellType.WALL,
    SENSOR_GOLD: CellType.GOLD,
}


class Sensor:
    """Inspects the cell in front of the robot."""

    def __init__(self, state: SimulationState) -> None:
        self._state = state

    def front_position(self) -> tuple[int, int]:
        """Coordinates of the cell directly ahead (may lie off the map)."""
        robot = self._state.robot
        deltaX, deltaY = robot.direction.delta
        return robot.x + deltaX, robot.y + deltaY

    def peek(self) -> CellType:
        """What lies ahead, for display only. Never marks the cell as discovered."""
        targetX, targetY = self.front_position()
        return self._state.world.cell_at(targetX, targetY)

    def is_there(self, cellKind: int) -> bool:
        """True if the cell ahead has the given kind (0 empty, 1 wall, 2 gold).

        The inspected cell becomes discovered. Off-map cells count as walls.
        """
        if cellKind not in _SENSOR_CELL_TYPES:
            raise BadArgError(f"isThere expects 0, 1 or 2, got {cellKind}")
        robot = self._state.robot
        world = self._state.world
        deltaX, deltaY = robot.direction.delta
        targetX, targetY = robot.x + deltaX, robot.y + deltaY
        world.mark_discovered(targetX, targetY)
        result = world.cell_at(targetX, targetY) is _SENSOR_CELL_TYPES[cellKind]
        robot.sensorResult = result
        robot.sensorTarget = (targetX, targetY)
        return result
