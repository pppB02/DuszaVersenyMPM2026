"""Editing operations on the block tree (insert, delete, move, field changes).

Temporarily wrong programs are allowed: unknown variables are accepted, only malformed
names/values and the nesting limit are refused. Semantic checks happen when running.
"""

from dataclasses import dataclass

from robot_ide.blocks.block_factory import blocks_from_statements, create_block
from robot_ide.blocks.block_models import (
    OPERATORS_BY_VALUE_KIND,
    Block,
    BlockKind,
    Branch,
    ValueBlock,
    ValueKind,
)
from robot_ide.core.constants import MAX_CONTROL_NESTING, MAX_NUMBER, MIN_NUMBER
from robot_ide.core.exceptions import BlockEditError
from robot_ide.parser.ast_nodes import StatementNode
from robot_ide.parser.syntax_validator import is_valid_identifier


def validate_variable_name(name: str) -> str:
    """Return the stripped name or raise ``BlockEditError`` (keyword, ``9lives``, ...)."""
    cleaned = name.strip()
    if not is_valid_identifier(cleaned):
        raise BlockEditError(f"invalid variable name: {name!r}")
    return cleaned


def _is_number(text: str) -> bool:
    return text.isascii() and text.isdigit() and MIN_NUMBER <= int(text) <= MAX_NUMBER


def validate_operand(text: str) -> str:
    """Operand = number 0..100, true/false or a variable name (which may not exist yet)."""
    cleaned = text.strip()
    if _is_number(cleaned) or cleaned in ("true", "false") or is_valid_identifier(cleaned):
        return cleaned
    raise BlockEditError(f"invalid value: {text!r}")


def validate_value(value: ValueBlock) -> ValueBlock:
    """Validate and normalize a value block."""
    if len(value.operands) != value.kind.operand_count:
        raise BlockEditError(f"{value.kind.value} needs {value.kind.operand_count} operand(s)")
    operands = [validate_operand(text) for text in value.operands]
    if value.kind is ValueKind.INTEGER and not _is_number(operands[0]):
        raise BlockEditError(f"not an integer 0..100: {value.operands[0]!r}")
    if value.kind is ValueKind.BOOLEAN and operands[0] not in ("true", "false"):
        raise BlockEditError(f"not a boolean: {value.operands[0]!r}")
    if value.kind is ValueKind.VARIABLE:
        validate_variable_name(operands[0])
    allowed = OPERATORS_BY_VALUE_KIND.get(value.kind)
    if allowed is not None and value.operator not in allowed:
        raise BlockEditError(f"operator not allowed for {value.kind.value}")
    if allowed is None and value.operator is not None:
        raise BlockEditError(f"{value.kind.value} has no operator")
    return ValueBlock(value.kind, operands, value.operator)


@dataclass(frozen=True)
class BlockLocation:
    """Where a block sits: parent (None = top level), branch and index."""

    parentId: int | None
    branch: Branch
    index: int


@dataclass
class _Found:
    block: Block
    parent: Block | None
    branch: Branch
    index: int
    ancestors: list[Block]


class BlockProgram:
    """Ordered top-level blocks plus all editing operations."""

    def __init__(self) -> None:
        self.blocks: list[Block] = []
        self._nextBlockId = 1

    def _allocate_id(self) -> int:
        blockId = self._nextBlockId
        self._nextBlockId += 1
        return blockId

    def clear(self) -> None:
        """Remove all blocks."""
        self.blocks = []

    def load_statements(self, statements: list[StatementNode]) -> None:
        """Replace the program by blocks made from parsed statements (all or nothing)."""
        self.blocks = blocks_from_statements(statements, self._allocate_id)

    def new_block(self, kind: BlockKind) -> Block:
        """Create a default block with a fresh id (not yet inserted)."""
        return create_block(kind, self._allocate_id())

    # ---- lookup -------------------------------------------------------------------------

    def _search(
        self,
        blockId: int,
        siblings: list[Block],
        parent: Block | None,
        branch: Branch,
        ancestors: list[Block],
    ) -> _Found | None:
        for index, block in enumerate(siblings):
            if block.blockId == blockId:
                return _Found(block, parent, branch, index, ancestors)
            for childBranch in (Branch.MAIN, Branch.ELSE):
                found = self._search(
                    blockId,
                    block.branch_blocks(childBranch),
                    block,
                    childBranch,
                    [*ancestors, block],
                )
                if found is not None:
                    return found
        return None

    def _require(self, blockId: int) -> _Found:
        found = self._search(blockId, self.blocks, None, Branch.MAIN, [])
        if found is None:
            raise BlockEditError(f"no such block: {blockId}")
        return found

    def find(self, blockId: int) -> Block:
        """Block by id."""
        return self._require(blockId).block

    def locate(self, blockId: int) -> BlockLocation:
        """Current position of a block."""
        found = self._require(blockId)
        parentId = found.parent.blockId if found.parent is not None else None
        return BlockLocation(parentId, found.branch, found.index)

    def _target(self, parentId: int | None, branch: Branch) -> tuple[list[Block], int]:
        """Child list and control depth of the chain ending at (and including) the parent."""
        if parentId is None:
            if branch is not Branch.MAIN:
                raise BlockEditError("top level has no else branch")
            return self.blocks, 0
        found = self._require(parentId)
        parent = found.block
        if not parent.kind.is_control:
            raise BlockEditError("only control blocks can contain blocks")
        if branch is Branch.ELSE and parent.kind is not BlockKind.IF_ELSE:
            raise BlockEditError("only if-else blocks have an else branch")
        depth = sum(1 for ancestor in found.ancestors if ancestor.kind.is_control) + 1
        return parent.branch_blocks(branch), depth

    # ---- structure edits ----------------------------------------------------------------

    def add_block(
        self,
        block: Block,
        parentId: int | None = None,
        branch: Branch = Branch.MAIN,
        index: int | None = None,
    ) -> None:
        """Insert a block (with its subtree). ``index=None`` appends."""
        siblings, depth = self._target(parentId, branch)
        if depth + block.control_depth() > MAX_CONTROL_NESTING:
            raise BlockEditError(f"control blocks may nest at most {MAX_CONTROL_NESTING} levels")
        position = len(siblings) if index is None else index
        if not 0 <= position <= len(siblings):
            raise BlockEditError(f"bad insert index: {index}")
        siblings.insert(position, block)

    def remove_block(self, blockId: int) -> Block:
        """Delete a block with its subtree and return it."""
        found = self._require(blockId)
        siblings = self.blocks if found.parent is None else found.parent.branch_blocks(found.branch)
        return siblings.pop(found.index)

    def move_block(
        self,
        blockId: int,
        parentId: int | None,
        branch: Branch = Branch.MAIN,
        index: int | None = None,
    ) -> None:
        """Move a block. ``index`` counts in the target list BEFORE the block is removed.

        On any error the block stays where it was.
        """
        found = self._require(blockId)
        if parentId is not None and parentId in {inner.blockId for inner in found.block.walk()}:
            raise BlockEditError("a block cannot be moved into itself")
        original = self.locate(blockId)
        block = self.remove_block(blockId)
        adjusted = index
        sameList = original.parentId == parentId and original.branch is branch
        if adjusted is not None and sameList and adjusted > original.index:
            adjusted -= 1
        try:
            self.add_block(block, parentId, branch, adjusted)
        except BlockEditError:
            self.add_block(block, original.parentId, original.branch, original.index)
            raise

    # ---- field edits --------------------------------------------------------------------

    def set_variable_name(self, blockId: int, name: str) -> None:
        """Rename the variable of a SET block."""
        block = self._require_kind(blockId, BlockKind.SET)
        block.variableName = validate_variable_name(name)

    def set_operand(self, blockId: int, text: str) -> None:
        """Change the operand of step/turn/print/if/while blocks."""
        block = self.find(blockId)
        if not block.kind.uses_operand:
            raise BlockEditError(f"{block.kind.value} has no operand")
        block.operand = validate_operand(text)

    def set_value(self, blockId: int, value: ValueBlock) -> None:
        """Replace the value of a SET block."""
        block = self._require_kind(blockId, BlockKind.SET)
        block.value = validate_value(value)

    def set_has_else(self, blockId: int, hasElse: bool) -> None:
        """Switch between ``if`` and ``if-else``. Removing a non-empty else is refused."""
        block = self.find(blockId)
        if block.kind not in (BlockKind.IF, BlockKind.IF_ELSE):
            raise BlockEditError("only if blocks can get an else branch")
        if hasElse:
            block.kind = BlockKind.IF_ELSE
        elif block.elseChildren:
            raise BlockEditError("move the blocks out of the else branch first")
        else:
            block.kind = BlockKind.IF

    def _require_kind(self, blockId: int, kind: BlockKind) -> Block:
        block = self.find(blockId)
        if block.kind is not kind:
            raise BlockEditError(f"block {blockId} is not a {kind.value} block")
        return block
