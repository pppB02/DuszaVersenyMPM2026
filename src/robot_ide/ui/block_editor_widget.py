"""Visual block editor: palette, block tree (drag and drop), edit dialog.

All changes go through :class:`BlockProgram`; this widget only shows the model.
"""

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from robot_ide.blocks.block_editor import (
    BlockProgram,
    validate_operand,
    validate_value,
    validate_variable_name,
)
from robot_ide.blocks.block_factory import create_value
from robot_ide.blocks.block_models import (
    OPERATORS_BY_VALUE_KIND,
    Block,
    BlockKind,
    Branch,
    ValueBlock,
    ValueKind,
)
from robot_ide.blocks.code_generator import header_text
from robot_ide.core.exceptions import BlockEditError
from robot_ide.ui.styles import LIGHT, BlockColors, block_colors

PALETTE_LABELS = {
    BlockKind.SET: "set",
    BlockKind.STEP_FORWARD: "step forward",
    BlockKind.TURN_BY: "turn by",
    BlockKind.MINE_HERE: "mine here",
    BlockKind.PRINT: "print",
    BlockKind.IF: "if",
    BlockKind.IF_ELSE: "if-else",
    BlockKind.WHILE: "while",
}
VALUE_LABELS = {
    ValueKind.INTEGER: "Egész szám",
    ValueKind.BOOLEAN: "Logikai érték",
    ValueKind.VARIABLE: "Változó",
    ValueKind.ARITHMETIC: "Aritmetikai művelet",
    ValueKind.COMPARISON: "Összehasonlítás",
    ValueKind.LOGICAL: "Logikai művelet",
    ValueKind.NOT: "not",
    ValueKind.IS_THERE: "isThere",
}
_ROLE = Qt.ItemDataRole.UserRole
InsertPoint = tuple[int | None, Branch, int | None]


class BlockEditDialog(QDialog):
    """Edit the fields of one block. ``apply`` validates everything before changing anything."""

    def __init__(self, block: Block, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Blokk szerkesztése")
        self._block = block
        form = QFormLayout()
        self._nameEdit = QLineEdit(block.variableName)
        self._operandEdit = QLineEdit(block.operand)
        self._kindCombo = QComboBox()
        self._operatorCombo = QComboBox()
        self._firstEdit = QLineEdit()
        self._secondEdit = QLineEdit()
        self._elseCheck = QCheckBox("else ág")
        self._elseCheck.setChecked(block.kind is BlockKind.IF_ELSE)
        if block.kind is BlockKind.SET:
            self._build_set_fields(form, block)
        elif block.kind.uses_operand:
            form.addRow("Érték:", self._operandEdit)
            if block.kind in (BlockKind.IF, BlockKind.IF_ELSE):
                form.addRow("", self._elseCheck)
        else:
            form.addRow(QLabel("Ennek a blokknak nincs szerkeszthető mezője."))
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _build_set_fields(self, form: QFormLayout, block: Block) -> None:
        assert block.value is not None
        form.addRow("Változó neve:", self._nameEdit)
        for kind, label in VALUE_LABELS.items():
            self._kindCombo.addItem(label, kind)
        self._kindCombo.setCurrentIndex(list(VALUE_LABELS).index(block.value.kind))
        form.addRow("Érték típusa:", self._kindCombo)
        form.addRow("Első operandus:", self._firstEdit)
        form.addRow("Művelet:", self._operatorCombo)
        form.addRow("Második operandus:", self._secondEdit)
        self._load_value(block.value)
        self._kindCombo.currentIndexChanged.connect(self._on_kind_changed)

    def _load_value(self, value: ValueBlock) -> None:
        self._operatorCombo.clear()
        for operator in OPERATORS_BY_VALUE_KIND.get(value.kind, ()):
            self._operatorCombo.addItem(operator.value, operator)
            if operator is value.operator:
                self._operatorCombo.setCurrentIndex(self._operatorCombo.count() - 1)
        self._firstEdit.setText(value.operands[0])
        self._secondEdit.setText(value.operands[1] if len(value.operands) > 1 else "")
        self._operatorCombo.setEnabled(value.kind in OPERATORS_BY_VALUE_KIND)
        self._secondEdit.setEnabled(value.kind.operand_count == 2)

    def _on_kind_changed(self) -> None:
        kind: ValueKind = self._kindCombo.currentData()
        self._load_value(create_value(kind))

    def _read_value(self) -> ValueBlock:
        kind: ValueKind = self._kindCombo.currentData()
        operands = [self._firstEdit.text()]
        if kind.operand_count == 2:
            operands.append(self._secondEdit.text())
        operator = self._operatorCombo.currentData() if kind in OPERATORS_BY_VALUE_KIND else None
        return ValueBlock(kind, operands, operator)

    def apply(self, program: BlockProgram) -> None:
        """Validate all fields, then change the block. Raises ``BlockEditError``."""
        block = self._block
        if block.kind is BlockKind.SET:
            name = validate_variable_name(self._nameEdit.text())
            value = validate_value(self._read_value())
            program.set_variable_name(block.blockId, name)
            program.set_value(block.blockId, value)
        elif block.kind.uses_operand:
            operand = validate_operand(self._operandEdit.text())
            if block.kind in (BlockKind.IF, BlockKind.IF_ELSE):
                program.set_has_else(block.blockId, self._elseCheck.isChecked())
            program.set_operand(block.blockId, operand)


class BlockTreeWidget(QTreeWidget):
    """Tree that reports drops instead of moving items itself (the model does the moving)."""

    dropRequested = Signal(object, object, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 (Qt API name)
        target = self.itemAt(event.position().toPoint())
        position = self.dropIndicatorPosition().name
        dragged = self.currentItem()
        event.ignore()
        self.dropRequested.emit(dragged, target, position)


class BlockEditorWidget(QWidget):
    """Palette + tree + action buttons. Emits ``programChanged`` after every edit."""

    programChanged = Signal()

    def __init__(self, program: BlockProgram, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._program = program
        self._colors: dict[str, BlockColors] = block_colors(LIGHT)
        self._items: dict[int, QTreeWidgetItem] = {}
        self._activeId: int | None = None
        self._tree = BlockTreeWidget()
        self._tree.dropRequested.connect(self._on_drop)
        self._tree.itemDoubleClicked.connect(lambda *_: self._edit_selected())
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._controls = QWidget()
        controlsLayout = QVBoxLayout(self._controls)
        controlsLayout.setContentsMargins(0, 0, 0, 0)
        controlsLayout.addWidget(QLabel("Új blokk (a kijelölés után):"))
        controlsLayout.addLayout(self._build_palette())
        controlsLayout.addLayout(self._build_action_buttons())
        layout = QVBoxLayout(self)
        layout.addWidget(self._controls)
        layout.addWidget(self._tree, 1)
        self.refresh()

    # ---- public API ---------------------------------------------------------------------

    def set_program(self, program: BlockProgram) -> None:
        """Edit another program (after load/new)."""
        self._program = program
        self._activeId = None
        self.refresh()

    def set_theme(self, theme: str) -> None:
        """Switch block colours."""
        self._colors = block_colors(theme)
        self.refresh()

    def set_editing_enabled(self, enabled: bool) -> None:
        """Lock the editor while a run is active."""
        self._controls.setEnabled(enabled)
        self._tree.setDragEnabled(enabled)
        self._tree.setAcceptDrops(enabled)

    def set_active_block(self, blockId: int | None) -> None:
        """Highlight the block that executes next."""
        previous = self._activeId
        self._activeId = blockId
        for changedId in (previous, blockId):
            item = self._items.get(changedId) if changedId is not None else None
            if item is not None and changedId is not None:
                self._style_item(item, self._program.find(changedId))

    def refresh(self) -> None:
        """Rebuild the tree from the model, keeping the selection."""
        selectedId = self._selected_block_id()
        self._tree.clear()
        self._items = {}
        self._build(self._program.blocks, self._tree.invisibleRootItem())
        self._tree.expandAll()
        if selectedId in self._items:
            self._tree.setCurrentItem(self._items[selectedId])

    # ---- building the view --------------------------------------------------------------

    def _build_palette(self) -> QGridLayout:
        grid = QGridLayout()
        for number, (kind, label) in enumerate(PALETTE_LABELS.items()):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, k=kind: self._add(k, "after"))
            grid.addWidget(button, number // 2, number % 2)
        return grid

    def _build_action_buttons(self) -> QGridLayout:
        grid = QGridLayout()
        actions: list[tuple[str, Callable[[], None]]] = [
            ("Szerkesztés", self._edit_selected),
            ("Törlés", self._delete_selected),
            ("▲ Fel", lambda: self._shift(-1)),
            ("▼ Le", lambda: self._shift(1)),
            ("⇥ Beljebb", self._indent_selected),
            ("⇤ Kiemelés", self._outdent_selected),
        ]
        for number, (label, handler) in enumerate(actions):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, h=handler: h())
            grid.addWidget(button, number // 2, number % 2)
        return grid

    def _build(self, blocks: list[Block], parentItem: QTreeWidgetItem) -> None:
        for block in blocks:
            item = QTreeWidgetItem(parentItem, [header_text(block)])
            item.setData(0, _ROLE, ("block", block.blockId))
            self._items[block.blockId] = item
            self._style_item(item, block)
            if block.kind is BlockKind.IF_ELSE:
                thenItem = self._branch_item(item, "then", block.blockId, Branch.MAIN)
                self._build(block.children, thenItem)
                elseItem = self._branch_item(item, "else", block.blockId, Branch.ELSE)
                self._build(block.elseChildren, elseItem)
            else:
                self._build(block.children, item)

    def _branch_item(
        self, parentItem: QTreeWidgetItem, label: str, ownerId: int, branch: Branch
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem(parentItem, [label])
        item.setData(0, _ROLE, ("branch", ownerId, branch))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        colors = self._colors["branch"]
        item.setBackground(0, QBrush(QColor(colors.background)))
        item.setForeground(0, QBrush(QColor(colors.text)))
        return item

    def _style_item(self, item: QTreeWidgetItem, block: Block) -> None:
        if block.blockId == self._activeId:
            colors = self._colors["active"]
        else:
            colors = self._colors["control" if block.kind.is_control else "command"]
        item.setBackground(0, QBrush(QColor(colors.background)))
        item.setForeground(0, QBrush(QColor(colors.text)))

    # ---- selection helpers --------------------------------------------------------------

    def _selected_payload(self) -> tuple | None:  # type: ignore[type-arg]
        item = self._tree.currentItem()
        return None if item is None else item.data(0, _ROLE)

    def _selected_block_id(self) -> int | None:
        payload = self._selected_payload()
        return payload[1] if payload is not None and payload[0] == "block" else None

    def _siblings(self, parentId: int | None, branch: Branch) -> list[Block]:
        if parentId is None:
            return self._program.blocks
        return self._program.find(parentId).branch_blocks(branch)

    # ---- edit actions -------------------------------------------------------------------

    def _apply(self, change: Callable[[], object]) -> None:
        """Run a model change; show a message instead of crashing if it is refused."""
        try:
            change()
        except BlockEditError as error:
            QMessageBox.warning(self, "A művelet nem engedélyezett", str(error))
            return
        self.refresh()
        self.programChanged.emit()

    def _insertion_point(self, position: str) -> InsertPoint:
        payload = self._selected_payload()
        if payload is None:
            return (None, Branch.MAIN, None)
        if payload[0] == "branch":
            return (payload[1], payload[2], None)
        blockId = payload[1]
        location = self._program.locate(blockId)
        if position == "before":
            return (location.parentId, location.branch, location.index)
        if position == "inside" and self._program.find(blockId).kind.is_control:
            return (blockId, Branch.MAIN, None)
        return (location.parentId, location.branch, location.index + 1)

    def _add(self, kind: BlockKind, position: str) -> None:
        def change() -> None:
            parentId, branch, index = self._insertion_point(position)
            self._program.add_block(self._program.new_block(kind), parentId, branch, index)

        self._apply(change)

    def _edit_selected(self) -> None:
        blockId = self._selected_block_id()
        if blockId is None or not self._controls.isEnabled():
            return
        dialog = BlockEditDialog(self._program.find(blockId), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._apply(lambda: dialog.apply(self._program))

    def _delete_selected(self) -> None:
        blockId = self._selected_block_id()
        if blockId is not None:
            self._apply(lambda: self._program.remove_block(blockId))

    def _shift(self, direction: int) -> None:
        blockId = self._selected_block_id()
        if blockId is None:
            return
        location = self._program.locate(blockId)
        count = len(self._siblings(location.parentId, location.branch))
        newIndex = location.index - 1 if direction < 0 else location.index + 2
        if newIndex < 0 or newIndex > count:
            return
        self._apply(
            lambda: self._program.move_block(blockId, location.parentId, location.branch, newIndex)
        )

    def _indent_selected(self) -> None:
        """Move into the previous sibling (it must be a control block)."""
        blockId = self._selected_block_id()
        if blockId is None:
            return
        location = self._program.locate(blockId)
        if location.index == 0:
            return
        previous = self._siblings(location.parentId, location.branch)[location.index - 1]
        self._apply(lambda: self._program.move_block(blockId, previous.blockId, Branch.MAIN, None))

    def _outdent_selected(self) -> None:
        """Lift out of the enclosing control block, right after that block."""
        blockId = self._selected_block_id()
        if blockId is None:
            return
        location = self._program.locate(blockId)
        if location.parentId is None:
            return
        parent = self._program.locate(location.parentId)
        self._apply(
            lambda: self._program.move_block(
                blockId, parent.parentId, parent.branch, parent.index + 1
            )
        )

    def _show_context_menu(self, point: object) -> None:
        if not self._controls.isEnabled():
            return
        menu = QMenu(self)
        for title, position in (
            ("Beszúrás elé", "before"),
            ("Beszúrás után", "after"),
            ("Beszúrás belülre", "inside"),
        ):
            submenu = menu.addMenu(title)
            for kind, label in PALETTE_LABELS.items():
                action = submenu.addAction(label)
                action.triggered.connect(
                    lambda _checked=False, k=kind, p=position: self._add(k, p)
                )
        menu.addSeparator()
        menu.addAction("Szerkesztés").triggered.connect(self._edit_selected)
        menu.addAction("Törlés").triggered.connect(self._delete_selected)
        menu.exec(self._tree.viewport().mapToGlobal(point))  # type: ignore[arg-type]

    # ---- drag and drop ------------------------------------------------------------------

    def _on_drop(
        self, dragged: QTreeWidgetItem | None, target: QTreeWidgetItem | None, position: str
    ) -> None:
        payload = None if dragged is None else dragged.data(0, _ROLE)
        if payload is None or payload[0] != "block":
            return
        blockId: int = payload[1]
        point = self._drop_point(target, position)
        if point is None:
            return
        parentId, branch, index = point
        self._apply(lambda: self._program.move_block(blockId, parentId, branch, index))

    def _drop_point(self, target: QTreeWidgetItem | None, position: str) -> InsertPoint | None:
        if target is None:
            return (None, Branch.MAIN, None)
        payload = target.data(0, _ROLE)
        if payload[0] == "branch":
            return (payload[1], payload[2], None) if position == "OnItem" else None
        targetId: int = payload[1]
        location = self._program.locate(targetId)
        if position == "AboveItem":
            return (location.parentId, location.branch, location.index)
        if position == "OnItem" and self._program.find(targetId).kind.is_control:
            return (targetId, Branch.MAIN, None)
        return (location.parentId, location.branch, location.index + 1)
