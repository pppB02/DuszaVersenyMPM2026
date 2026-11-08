"""Drives a :class:`DebugSession` from a Qt timer: run, pause, continue, step, stop.

Each timer tick executes a small batch of program lines, so the GUI never blocks. A run is
capped at 1000 executed lines, so a worker thread is not needed.
"""

from enum import Enum

from PySide6.QtCore import QObject, QTimer, Signal

from robot_ide.services.debug_session import DebugSession

# speed level 1..10 -> delay between lines in milliseconds (0 = as fast as possible)
SPEED_DELAYS_MS = {1: 1000, 2: 600, 3: 400, 4: 250, 5: 150, 6: 80, 7: 40, 8: 20, 9: 5, 10: 0}
DEFAULT_SPEED = 5
_FAST_BATCH = 25


class RunnerState(Enum):
    """Controller state."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class RunController(QObject):
    """Timer-driven execution. ``updated`` fires after every change, ``finished`` at the end."""

    updated = Signal()
    finished = Signal()

    def __init__(self, session: DebugSession, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._delayMs = SPEED_DELAYS_MS[DEFAULT_SPEED]
        self.state = RunnerState.IDLE
        self.lastProgramText: str | None = None
        self.lastModeIsDebug = False

    @property
    def is_active(self) -> bool:
        """True while a run is running or paused."""
        return self.state in (RunnerState.RUNNING, RunnerState.PAUSED)

    def set_speed(self, level: int) -> None:
        """Set speed level 1..10."""
        self._delayMs = SPEED_DELAYS_MS[max(1, min(10, level))]
        if self.state is RunnerState.RUNNING:
            self._timer.start(self._delayMs)

    def run(self, programText: str) -> None:
        """Start a new automatic run."""
        if self._begin(programText, debug=False):
            self.state = RunnerState.RUNNING
            self._timer.start(self._delayMs)
            self.updated.emit()

    def debug(self, programText: str) -> None:
        """Start a new run paused on its first line (step-by-step mode)."""
        if self._begin(programText, debug=True):
            self.state = RunnerState.PAUSED
            self.updated.emit()

    def restart(self) -> None:
        """Run again with the same program and mode."""
        if self.lastProgramText is None:
            return
        if self.lastModeIsDebug:
            self.debug(self.lastProgramText)
        else:
            self.run(self.lastProgramText)

    def pause(self) -> None:
        """Pause an automatic run."""
        if self.state is RunnerState.RUNNING:
            self._timer.stop()
            self.state = RunnerState.PAUSED
            self.updated.emit()

    def resume(self) -> None:
        """Continue automatic execution from a pause."""
        if self.state is RunnerState.PAUSED:
            self.state = RunnerState.RUNNING
            self._timer.start(self._delayMs)
            self.updated.emit()

    def step(self) -> None:
        """Execute exactly one line while paused."""
        if self.state is RunnerState.PAUSED:
            self._session.step()
            self._after_advance()

    def stop(self) -> None:
        """Abort the run."""
        if self.is_active:
            self._timer.stop()
            self._session.stop()
            self._finish()

    def sync_after_external_stop(self) -> None:
        """Bring the controller in line after the session was stopped by manual control."""
        if self.is_active and not self._session.is_active:
            self._timer.stop()
            self._finish()

    def _begin(self, programText: str, debug: bool) -> bool:
        self._timer.stop()
        self.lastProgramText = programText
        self.lastModeIsDebug = debug
        self._session.start(programText)
        if not self._session.is_active:
            self._finish()
            return False
        return True

    def _tick(self) -> None:
        batch = _FAST_BATCH if self._delayMs < 20 else 1
        for _ in range(batch):
            if not self._session.step():
                break
        self._after_advance()

    def _after_advance(self) -> None:
        if self._session.is_active:
            self.updated.emit()
        else:
            self._finish()

    def _finish(self) -> None:
        self._timer.stop()
        self.state = RunnerState.FINISHED
        self.updated.emit()
        self.finished.emit()
