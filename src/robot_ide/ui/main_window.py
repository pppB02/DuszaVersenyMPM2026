"""Main window: wires panels, actions, project model and run controller together."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from robot_ide.blocks.code_generator import GeneratedCode
from robot_ide.core.enums import RunStatus
from robot_ide.core.exceptions import BlockEditError, InputFormatError, MineScriptSyntaxError
from robot_ide.services.debug_session import DebugSession
from robot_ide.services.file_service import read_text, write_text
from robot_ide.services.manual_control import ManualControlService, ManualResult
from robot_ide.services.project_service import ProjectService
from robot_ide.ui.block_editor_widget import BlockEditorWidget
from robot_ide.ui.console_widget import ConsoleWidget
from robot_ide.ui.debugger_widget import DebuggerWidget
from robot_ide.ui.manual_control_widget import ManualControlWidget
from robot_ide.ui.map_widget import MapWidget
from robot_ide.ui.robot_widget import RobotStatusWidget
from robot_ide.ui.run_controller import RunController, RunnerState
from robot_ide.ui.source_code_widget import SourceCodeWidget
from robot_ide.ui.styles import DARK, LIGHT, stylesheet
from robot_ide.ui.toolbar import create_toolbar
from robot_ide.ui.variable_widget import VariableWidget

_FILE_FILTER = "MineScript bemenet (*.txt);;Minden fájl (*)"
_FINAL_STATE_TEXT = {
    RunStatus.COMPLETED: "Kész",
    RunStatus.LIMIT_EXCEEDED: "Utasításlimit túllépve",
    RunStatus.SYNTAX_ERROR: "Szintaxishiba",
    RunStatus.STOPPED: "Leállítva",
}


class MainWindow(QMainWindow):
    """The IDE window. Business logic stays in services; this class only connects things."""

    def __init__(self, project: ProjectService, outputPath: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle("MineScript Robot IDE")
        self.resize(1280, 800)
        self._project = project
        self._outputPath = outputPath
        self._currentFile: Path | None = None
        self._theme = LIGHT
        self._code = GeneratedCode()
        self._session = DebugSession(project.simulation)
        self._controller = RunController(self._session, self)
        self._manual = ManualControlService(self._session)
        self._manualMode = False

        self._blocks = BlockEditorWidget(project.program)
        self._source = SourceCodeWidget()
        self._map = MapWidget()
        self._status = RobotStatusWidget()
        self._debugger = DebuggerWidget()
        self._variables = VariableWidget()
        self._console = ConsoleWidget()
        self._manualPanel = ManualControlWidget()
        self._revealCheck = QCheckBox("Teljes térkép mutatása")
        self._docks: dict[str, QDockWidget] = {}
        self._build_layout()
        self._build_actions()
        self._connect_signals()
        self._apply_theme(LIGHT)
        self._after_project_replaced()

    # ---- construction -------------------------------------------------------------------

    def _build_layout(self) -> None:
        center = QWidget()
        centerLayout = QVBoxLayout(center)
        centerLayout.addWidget(self._map, 1)
        centerLayout.addWidget(self._revealCheck)
        centerLayout.addWidget(self._status)
        self.setCentralWidget(center)
        left = Qt.DockWidgetArea.LeftDockWidgetArea
        right = Qt.DockWidgetArea.RightDockWidgetArea
        bottom = Qt.DockWidgetArea.BottomDockWidgetArea
        self._docks["blocks"] = self._add_dock("Blokkszerkesztő", self._blocks, left)
        self._docks["source"] = self._add_dock("Forráskód", self._source, left)
        self._docks["manual"] = self._add_dock("Kézi vezérlés", self._manualPanel, right)
        self._docks["debugger"] = self._add_dock("Debugger", self._debugger, right)
        self._docks["variables"] = self._add_dock("Változók", self._variables, right)
        self._docks["console"] = self._add_dock("Konzol / Napló / Hibák", self._console, bottom)
        self.splitDockWidget(self._docks["blocks"], self._docks["source"], Qt.Orientation.Vertical)
        self.splitDockWidget(
            self._docks["debugger"], self._docks["variables"], Qt.Orientation.Vertical
        )

    def _add_dock(self, title: str, widget: QWidget, area: Qt.DockWidgetArea) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setObjectName(title)
        dock.setWidget(widget)
        self.addDockWidget(area, dock)
        return dock

    def _make_action(
        self, text: str, handler: Callable[[], object], shortcut: str | None = None
    ) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(lambda _checked=False: handler())
        return action

    def _build_actions(self) -> None:
        self._newAction = self._make_action("Új", self._new_project, "Ctrl+N")
        self._openAction = self._make_action("Megnyitás", self._open_dialog, "Ctrl+O")
        self._saveAction = self._make_action("Mentés", self._save, "Ctrl+S")
        self._saveAsAction = self._make_action("Mentés másként...", self._save_as, "Ctrl+Shift+S")
        self._runAction = self._make_action("▶ Futás", self._start_run, "F5")
        self._pauseAction = self._make_action("⏸ Szünet", self._controller.pause, "F6")
        self._continueAction = self._make_action("⏵ Folytatás", self._controller.resume, "F8")
        self._stepAction = self._make_action("⏭ Lépés", self._step, "F10")
        self._stopAction = self._make_action("⏹ Leállítás", self._controller.stop, "Shift+F5")
        self._restartAction = self._make_action("⟲ Újraindítás", self._restart, "Ctrl+F5")
        themeAction = self._make_action("Világos/sötét téma", self._toggle_theme)
        aboutAction = self._make_action("Névjegy", self._about)

        fileMenu = self.menuBar().addMenu("Fájl")
        for action in (self._newAction, self._openAction, self._saveAction, self._saveAsAction):
            fileMenu.addAction(action)
        fileMenu.addSeparator()
        fileMenu.addAction(self._make_action("Kilépés", self.close, "Ctrl+Q"))
        runMenu = self.menuBar().addMenu("Futás")
        for action in (self._runAction, self._pauseAction, self._continueAction,
                       self._stepAction, self._stopAction, self._restartAction):
            runMenu.addAction(action)
        viewMenu = self.menuBar().addMenu("Nézet")
        for dock in self._docks.values():
            viewMenu.addAction(dock.toggleViewAction())
        viewMenu.addSeparator()
        viewMenu.addAction(themeAction)
        self.menuBar().addMenu("Súgó").addAction(aboutAction)

        toolbar, self._speedSlider = create_toolbar(
            self,
            [self._newAction, self._openAction, self._saveAction, None, self._runAction,
             self._pauseAction, self._continueAction, self._stepAction, self._stopAction,
             self._restartAction],
        )
        self.addToolBar(toolbar)

    def _connect_signals(self) -> None:
        self._blocks.programChanged.connect(self._refresh_source)
        self._controller.updated.connect(self._refresh_run_views)
        self._controller.finished.connect(self._on_run_finished)
        self._speedSlider.valueChanged.connect(self._controller.set_speed)
        self._revealCheck.toggled.connect(self._map.set_reveal_all)
        panel = self._manualPanel
        manual = self._manual
        panel.forwardRequested.connect(lambda: self._manual_action(manual.step_forward))
        panel.turnRequested.connect(
            lambda count: self._manual_action(lambda: manual.turn_left(count))
        )
        panel.mineRequested.connect(lambda: self._manual_action(manual.mine_here))

    # ---- project / files ----------------------------------------------------------------

    def open_path(self, path: Path) -> None:
        """Load an input file (map + program); show an error dialog if it is invalid."""
        try:
            self._project.load_text(read_text(path))
        except (OSError, UnicodeDecodeError, InputFormatError, MineScriptSyntaxError,
                BlockEditError) as error:
            QMessageBox.critical(self, "A fájl nem tölthető be", f"{path}\n\n{error}")
            return
        self._currentFile = path
        self._after_project_replaced()

    def _open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Megnyitás", "", _FILE_FILTER)
        if path:
            self.open_path(Path(path))

    def _save(self) -> None:
        if self._currentFile is None:
            self._save_as()
        else:
            self._write_project(self._currentFile)

    def _save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Mentés másként", "", _FILE_FILTER)
        if path:
            self._currentFile = Path(path)
            self._write_project(self._currentFile)

    def _write_project(self, path: Path) -> None:
        try:
            write_text(path, self._project.to_input_text())
        except OSError as error:
            QMessageBox.critical(self, "A mentés nem sikerült", str(error))

    def _new_project(self) -> None:
        self._project.new_project()
        self._currentFile = None
        self._after_project_replaced()

    def _after_project_replaced(self) -> None:
        self._manualMode = False
        self._controller.stop()
        self._session.set_simulation(self._project.simulation)
        self._map.set_simulation(self._project.simulation)
        self._blocks.set_program(self._project.program)
        self._console.clear_all()
        self._refresh_source()
        self._refresh_run_views()

    # ---- run control --------------------------------------------------------------------

    def _refresh_source(self) -> None:
        self._code = self._project.generated_code()
        self._source.show_code(self._code.lines)

    def _manual_action(self, action: Callable[[], ManualResult]) -> None:
        """Run one manual action; it stops an active program run first (no reset, no log)."""
        self._manualMode = True
        result = action()
        self._manualPanel.show_feedback(result.message)
        self.statusBar().showMessage(result.message, 4000)
        self._controller.sync_after_external_stop()
        self._refresh_run_views()

    def _start_run(self) -> None:
        self._manualMode = False
        self._console.clear_all()
        self._controller.run(self._code.text)

    def _restart(self) -> None:
        self._manualMode = False
        self._console.clear_all()
        self._controller.restart()

    def _step(self) -> None:
        if self._controller.state is RunnerState.PAUSED:
            self._controller.step()
        elif not self._controller.is_active:
            self._manualMode = False
            self._console.clear_all()
            self._controller.debug(self._code.text)

    def _on_run_finished(self) -> None:
        self._console.show_errors(self._error_messages())
        if self._outputPath is not None:
            try:
                write_text(self._outputPath, self._session.logText)
            except OSError as error:
                self._console.show_errors([f"A naplófájl nem írható: {error}"])

    def _error_messages(self) -> list[str]:
        session = self._session
        if session.syntaxError is not None:
            return [
                f"Szintaxishiba (sor {session.syntaxError.lineNumber}): "
                f"{session.syntaxError.description}"
            ]
        error = session.runtimeError
        if error is not None:
            return [f"{error.errorCode.value} (sor {error.lineNumber}): {error.description}"]
        if session.status is RunStatus.LIMIT_EXCEEDED:
            return ["INSTRUCTION_COUNT_LIMIT_EXCEEDED"]
        return []

    def _state_text(self) -> str:
        state = self._controller.state
        if state is RunnerState.IDLE:
            return "Készenlét"
        if state is RunnerState.RUNNING:
            return "Fut"
        if state is RunnerState.PAUSED:
            return "Szünetel"
        if self._manualMode:
            return "Kézi vezérlés"
        error = self._session.runtimeError
        if error is not None:
            return f"Hiba: {error.errorCode.value}"
        return _FINAL_STATE_TEXT.get(self._session.status or RunStatus.COMPLETED, "Kész")

    def _refresh_run_views(self) -> None:
        session = self._session
        simulation = self._project.simulation
        stateText = self._state_text()
        self._map.update()
        self._status.update_from(simulation, stateText)
        self._variables.show_variables(session.variables)
        self._debugger.update_info(
            session.currentLine, session.executedLines, simulation, stateText
        )
        self._console.show_output(session.printedOutput)
        self._console.show_log(session.logText)
        self._source.highlight_line(session.currentLine)
        line = session.currentLine
        self._blocks.set_active_block(None if line is None else self._code.block_at_line(line))
        self._update_controls()

    def _update_controls(self) -> None:
        state = self._controller.state
        idle = state in (RunnerState.IDLE, RunnerState.FINISHED)
        self._runAction.setEnabled(idle)
        self._pauseAction.setEnabled(state is RunnerState.RUNNING)
        self._continueAction.setEnabled(state is RunnerState.PAUSED)
        self._stepAction.setEnabled(idle or state is RunnerState.PAUSED)
        self._stopAction.setEnabled(self._controller.is_active)
        self._restartAction.setEnabled(
            self._controller.lastProgramText is not None and state is not RunnerState.RUNNING
        )
        self._newAction.setEnabled(idle)
        self._openAction.setEnabled(idle)
        self._blocks.set_editing_enabled(idle)

    # ---- misc ---------------------------------------------------------------------------

    def _toggle_theme(self) -> None:
        self._apply_theme(LIGHT if self._theme == DARK else DARK)

    def _apply_theme(self, theme: str) -> None:
        self._theme = theme
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(stylesheet(theme))
        self._map.set_theme(theme)
        self._blocks.set_theme(theme)
        self._source.set_highlight_color("#854d0e" if theme == DARK else "#fde68a")

    def _about(self) -> None:
        QMessageBox.about(self, "Névjegy", "MineScript Robot IDE\nSaját MineScript interpreterrel.")
