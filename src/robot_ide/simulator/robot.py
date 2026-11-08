"""Robot actions. All state lives in :class:`SimulationState`."""

from robot_ide.core.enums import CellType
from robot_ide.core.exceptions import BadArgError, BedrockHitError, NoGoldError
from robot_ide.simulator.simulation_state import SimulationState


class Robot:
    """Executes robot actions against the central simulation state."""

    def __init__(self, state: SimulationState) -> None:
        self._state = state

    def step_forward(self, count: int) -> None:
        """Move ``count`` cells ahead, discovering every cell on the way.

        The robot advances one cell at a time. If the next cell is a wall or off the map,
        it stays on the last free cell and ``BedrockHitError`` is raised.
        """
        if count < 0:
            raise BadArgError(f"step count must not be negative: {count}")
        robot = self._state.robot
        world = self._state.world
        deltaX, deltaY = robot.direction.delta
        for _ in range(count):
            nextX, nextY = robot.x + deltaX, robot.y + deltaY
            if world.cell_at(nextX, nextY) is CellType.WALL:
                raise BedrockHitError(f"wall or map edge at ({nextX}, {nextY})")
            robot.x, robot.y = nextX, nextY
            world.mark_discovered(nextX, nextY)

    def turn_by(self, quarterTurns: int) -> None:
        """Turn left by ``quarterTurns`` quarter turns (counter-clockwise, modulo 4)."""
        if quarterTurns < 0:
            raise BadArgError(f"turn count must not be negative: {quarterTurns}")
        robot = self._state.robot
        robot.direction = robot.direction.turned_left(quarterTurns)

    def mine_here(self) -> None:
        """Mine the gold on the current cell."""
        robot = self._state.robot
        world = self._state.world
        if world.cell_at(robot.x, robot.y) is not CellType.GOLD:
            raise NoGoldError(f"no gold at ({robot.x}, {robot.y})")
        world.clear_gold(robot.x, robot.y)
        robot.minedGold += 1
