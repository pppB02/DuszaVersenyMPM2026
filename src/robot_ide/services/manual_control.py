"""Manual robot control: single actions on the central simulation, no program log.

Every action first takes over from an active program run (the run is stopped, the simulation
is NOT reset). Movement, turning and mining reuse :class:`Robot`; nothing is duplicated.
"""

from dataclasses import dataclass

from robot_ide.core.enums import CellType
from robot_ide.core.exceptions import BadArgError, NoGoldError
from robot_ide.services.debug_session import DebugSession
from robot_ide.simulator.robot import Robot
from robot_ide.simulator.sensor import Sensor

MESSAGE_WALL_AHEAD = "Fal előtt – a robot megállt."
MESSAGE_NO_GOLD = "Nincs arany az aktuális mezőn."
MESSAGE_MINED = "Arany kibányászva."
MESSAGE_MOVED = "Előrelépés."
MESSAGE_TURNED = "Fordulás balra."
MESSAGE_BAD_TURN = "A fordulás paramétere nem lehet negatív."


@dataclass(frozen=True)
class ManualResult:
    """Outcome of one manual action. A refused action is not an error: state is unchanged."""

    succeeded: bool
    message: str


class ManualControlService:
    """Executes manual actions against the session's simulation."""

    def __init__(self, session: DebugSession) -> None:
        self._session = session

    def _take_over(self) -> Robot:
        """Stop an active program run and return a robot bound to the live simulation."""
        self._session.stop()
        return Robot(self._session.simulation)

    def step_forward(self) -> ManualResult:
        """Step one cell ahead if it is free. A wall or the map edge only gives a message.

        The wall check reads the map directly. ``isThere`` is not used, because it would
        mark the cell as discovered.
        """
        robot = self._take_over()
        simulation = self._session.simulation
        targetX, targetY = Sensor(simulation).front_position()
        if simulation.world.cell_at(targetX, targetY) is CellType.WALL:
            return ManualResult(False, MESSAGE_WALL_AHEAD)
        robot.step_forward(1)
        return ManualResult(True, MESSAGE_MOVED)

    def turn_left(self, quarterTurns: int = 1) -> ManualResult:
        """Turn left by ``quarterTurns`` quarter turns (0 changes nothing)."""
        robot = self._take_over()
        try:
            robot.turn_by(quarterTurns)
        except BadArgError:
            return ManualResult(False, MESSAGE_BAD_TURN)
        return ManualResult(True, MESSAGE_TURNED)

    def mine_here(self) -> ManualResult:
        """Mine the gold on the current cell, or report that there is none."""
        robot = self._take_over()
        try:
            robot.mine_here()
        except NoGoldError:
            return ManualResult(False, MESSAGE_NO_GOLD)
        return ManualResult(True, MESSAGE_MINED)
