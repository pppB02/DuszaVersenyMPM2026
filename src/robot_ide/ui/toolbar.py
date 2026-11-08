"""Main toolbar with run controls and the speed slider."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QSlider, QToolBar, QWidget

from robot_ide.ui.run_controller import DEFAULT_SPEED


def create_toolbar(parent: QWidget, actions: list[QAction | None]) -> tuple[QToolBar, QSlider]:
    """Build the toolbar; ``None`` entries become separators. Returns (toolbar, speed slider)."""
    toolbar = QToolBar("Eszköztár", parent)
    toolbar.setMovable(False)
    for action in actions:
        if action is None:
            toolbar.addSeparator()
        else:
            toolbar.addAction(action)
    toolbar.addSeparator()
    toolbar.addWidget(QLabel(" Sebesség "))
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(1, 10)
    slider.setValue(DEFAULT_SPEED)
    slider.setFixedWidth(140)
    toolbar.addWidget(slider)
    return toolbar, slider
