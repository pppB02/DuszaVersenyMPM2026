"""Block tree -> MineScript text (exactly one text per block structure)."""

from collections.abc import Sequence
from dataclasses import dataclass, field

from robot_ide.blocks.block_models import Block, BlockKind, ValueBlock, ValueKind

INDENT = "  "


@dataclass
class GeneratedCode:
    """Generated program text plus the block <-> line mapping (1-based lines)."""

    lines: list[str] = field(default_factory=list)
    lineByBlockId: dict[int, int] = field(default_factory=dict)
    elseLineByBlockId: dict[int, int] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Program text without trailing newline."""
        return "\n".join(self.lines)

    def block_at_line(self, lineNumber: int) -> int | None:
        """Id of the block whose header (or else) is on this line."""
        for blockId, line in self.lineByBlockId.items():
            if line == lineNumber:
                return blockId
        for blockId, line in self.elseLineByBlockId.items():
            if line == lineNumber:
                return blockId
        return None


def value_text(value: ValueBlock) -> str:
    """Right-hand side text of a SET block."""
    if value.kind in (ValueKind.INTEGER, ValueKind.BOOLEAN, ValueKind.VARIABLE):
        return value.operands[0]
    if value.kind is ValueKind.NOT:
        return f"not {value.operands[0]}"
    if value.kind is ValueKind.IS_THERE:
        return f"isThere {value.operands[0]}"
    assert value.operator is not None
    return f"{value.operands[0]} {value.operator.value} {value.operands[1]}"


def header_text(block: Block) -> str:
    """The single source line a block produces (without indentation)."""
    kind = block.kind
    if kind is BlockKind.SET:
        assert block.value is not None
        return f"set {block.variableName} to {value_text(block.value)}"
    if kind is BlockKind.STEP_FORWARD:
        return f"step forward {block.operand}"
    if kind is BlockKind.TURN_BY:
        return f"turn by {block.operand}"
    if kind is BlockKind.MINE_HERE:
        return "mine here"
    if kind is BlockKind.PRINT:
        return f"print {block.operand}"
    if kind is BlockKind.WHILE:
        return f"while {block.operand}"
    return f"if {block.operand}"


def generate_code(blocks: Sequence[Block]) -> GeneratedCode:
    """Generate program text with exact indentation."""
    generated = GeneratedCode()
    _emit(blocks, 0, generated)
    return generated


def _emit(blocks: Sequence[Block], depth: int, generated: GeneratedCode) -> None:
    prefix = INDENT * depth
    for block in blocks:
        generated.lines.append(prefix + header_text(block))
        generated.lineByBlockId[block.blockId] = len(generated.lines)
        _emit(block.children, depth + 1, generated)
        if block.kind is BlockKind.IF_ELSE:
            generated.lines.append(prefix + "else")
            generated.elseLineByBlockId[block.blockId] = len(generated.lines)
            _emit(block.elseChildren, depth + 1, generated)
