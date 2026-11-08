"""GUI start-up."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from robot_ide.services.project_service import ProjectService
from robot_ide.ui.main_window import MainWindow


def run_gui(inputPath: Path | None, outputPath: Path | None) -> int:
    """Open the IDE, optionally with an input file and a log output file."""
    app = QApplication(sys.argv[:1])
    window = MainWindow(ProjectService(), outputPath)
    if inputPath is not None:
        window.open_path(inputPath)
    window.show()
    return app.exec()
