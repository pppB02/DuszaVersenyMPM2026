"""Central simulation model: the only owner of world and robot state."""

from dataclasses import dataclass

from robot_ide.core.enums import Direction
from robot_ide.simulator.world import World


@dataclass
class RobotState:
    """Everything known about the robot."""

    x: int
    y: int
    direction: Direction
    minedGold: int = 0
    sensorResult: bool | None = None
    sensorTarget: tuple[int, int] | None = None

    def copy(self) -> "RobotState":
        """Independent copy."""
        return RobotState(
            self.x, self.y, self.direction, self.minedGold, self.sensorResult, self.sensorTarget
        )


class SimulationState:
    """World plus robot, with a stored initial snapshot for reliable resets."""

    def __init__(self, world: World, robot: RobotState) -> None:
        self.world = world
        self.robot = robot
        self._initialWorld = world.copy()
        self._initialRobot = robot.copy()

    def initial_snapshot(self) -> tuple[World, RobotState]:
        """Copies of the initial world and robot (used to save the map)."""
        return self._initialWorld.copy(), self._initialRobot.copy()

    def reset(self) -> None:
        """Restore map, robot, gold counter and discovery to the initial state."""
        self.world = self._initialWorld.copy()
        self.robot = self._initialRobot.copy()
