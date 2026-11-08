"""Manual control panel: three buttons and a turn-count field. No robot logic here."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

MAX_TURN_COUNT = 1000


class ManualControlWidget(QGroupBox):
    """Emits one signal per button press; the main window forwards them to the service."""

    forwardRequested = Signal()
    turnRequested = Signal(int)
    mineRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Kézi vezérlés", parent)
        forwardButton = QPushButton("Előre 1 mezőt")
        turnButton = QPushButton("Fordulás balra")
        mineButton = QPushButton("Arany kibányászása")
        self._turnCount = QSpinBox()
        self._turnCount.setRange(0, MAX_TURN_COUNT)
        self._turnCount.setValue(1)
        self._feedback = QLabel("")
        self._feedback.setWordWrap(True)
        turnRow = QHBoxLayout()
        turnRow.addWidget(turnButton, 1)
        turnRow.addWidget(QLabel("n ="))
        turnRow.addWidget(self._turnCount)
        layout = QVBoxLayout(self)
        layout.addWidget(forwardButton)
        layout.addLayout(turnRow)
        layout.addWidget(mineButton)
        layout.addWidget(self._feedback)
        forwardButton.clicked.connect(lambda _checked=False: self.forwardRequested.emit())
        turnButton.clicked.connect(
            lambda _checked=False: self.turnRequested.emit(self.turn_count())
        )
        mineButton.clicked.connect(lambda _checked=False: self.mineRequested.emit())

    def turn_count(self) -> int:
        """Value of the turn parameter field (never negative)."""
        return self._turnCount.value()

    def show_feedback(self, message: str) -> None:
        """Short result text under the buttons."""
        self._feedback.setText(message)
