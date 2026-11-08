"""Themes: stylesheet, block colours and map colours."""

from dataclasses import dataclass

LIGHT = "light"
DARK = "dark"


@dataclass(frozen=True)
class MapColors:
    """Colours used by the map widget (hex strings)."""

    background: str
    wall: str
    emptyDiscovered: str
    emptyHidden: str
    gold: str
    robot: str
    sensor: str
    grid: str
    text: str


@dataclass(frozen=True)
class BlockColors:
    """Background and text colour of one block category."""

    background: str
    text: str


def map_colors(theme: str) -> MapColors:
    """Map colours for a theme."""
    if theme == DARK:
        return MapColors(
            "#11151c", "#4b5563", "#2f3b4d", "#1a212c", "#facc15", "#38bdf8", "#f97316",
            "#0b0e13", "#cbd5e1",
        )
    return MapColors(
        "#e5e7eb", "#4b5563", "#f8fafc", "#9ca3af", "#eab308", "#2563eb", "#ea580c",
        "#cbd5e1", "#111827",
    )


def block_colors(theme: str) -> dict[str, BlockColors]:
    """Colours per category: command, control, branch label, active (executing)."""
    if theme == DARK:
        return {
            "command": BlockColors("#1e3a5f", "#e0ecff"),
            "control": BlockColors("#6b3f12", "#ffeccf"),
            "branch": BlockColors("#3b2a14", "#ffeccf"),
            "active": BlockColors("#166534", "#f0fdf4"),
        }
    return {
        "command": BlockColors("#dbeafe", "#0f2a52"),
        "control": BlockColors("#fed7aa", "#5a2d02"),
        "branch": BlockColors("#ffedd5", "#5a2d02"),
        "active": BlockColors("#bbf7d0", "#052e16"),
    }


def stylesheet(theme: str) -> str:
    """Application stylesheet."""
    if theme == DARK:
        base, panel, text, border, accent, hover = (
            "#0f141b", "#171d27", "#e2e8f0", "#2b3544", "#38bdf8", "#223044",
        )
    else:
        base, panel, text, border, accent, hover = (
            "#f1f5f9", "#ffffff", "#0f172a", "#cbd5e1", "#2563eb", "#e2e8f0",
        )
    return f"""
    QMainWindow, QDialog {{ background: {base}; color: {text}; }}
    QWidget {{ color: {text}; font-size: 13px; }}
    QDockWidget {{ font-weight: 600; }}
    QDockWidget::title {{ background: {panel}; padding: 6px; border: 1px solid {border}; }}
    QTreeWidget, QPlainTextEdit, QTableWidget, QTabWidget::pane, QLineEdit, QComboBox {{
        background: {panel}; border: 1px solid {border}; border-radius: 6px;
    }}
    QPlainTextEdit {{ font-family: Consolas, "DejaVu Sans Mono", monospace; }}
    QPushButton, QToolButton {{
        background: {panel}; border: 1px solid {border}; border-radius: 6px; padding: 5px 10px;
    }}
    QPushButton:hover, QToolButton:hover {{ background: {hover}; border-color: {accent}; }}
    QPushButton:disabled, QToolButton:disabled {{ color: #94a3b8; }}
    QToolBar {{ background: {panel}; border-bottom: 1px solid {border}; spacing: 4px; }}
    QMenuBar, QStatusBar {{ background: {panel}; }}
    QMenu {{ background: {panel}; border: 1px solid {border}; }}
    QMenu::item:selected {{ background: {hover}; }}
    QHeaderView::section {{ background: {panel}; border: 0; border-bottom: 1px solid {border}; }}
    QTabBar::tab {{ padding: 5px 12px; border: 1px solid {border}; border-bottom: 0; }}
    QTabBar::tab:selected {{ background: {panel}; color: {accent}; }}
    """
