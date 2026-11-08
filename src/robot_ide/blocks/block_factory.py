"""Creation of blocks: defaults for the palette and conversion from a parsed AST."""

from collections.abc import Callable, Sequence

from robot_ide.blocks.block_models import (
    ARITHMETIC_OPERATORS,
    COMPARISON_OPERATORS,
    LOGICAL_OPERATORS,
    Block,
    BlockKind,
    ValueBlock,
    ValueKind,
)
from robot_ide.core.constants import MAX_CONTROL_NESTING
from robot_ide.core.enums import Operator
from robot_ide.core.exceptions import BlockEditError
from robot_ide.core.models import format_value
from robot_ide.parser.ast_nodes import (
    BinaryNode,
    ExpressionNode,
    IfNode,
    IsThereNode,
    LiteralNode,
    MineHereNode,
    PrintNode,
    SetNode,
    StatementNode,
    StepForwardNode,
    TurnByNode,
    UnaryNode,
    VariableNode,
    WhileNode,
)

_DEFAULT_OPERANDS = {
    BlockKind.STEP_FORWARD: "1",
    BlockKind.TURN_BY: "1",
    BlockKind.PRINT: "0",
    BlockKind.IF: "true",
    BlockKind.IF_ELSE: "true",
    BlockKind.WHILE: "true",
}


def create_value(kind: ValueKind) -> ValueBlock:
    """Default value block of the given kind (always valid)."""
    if kind is ValueKind.INTEGER:
        return ValueBlock(kind, ["0"])
    if kind is ValueKind.BOOLEAN:
        return ValueBlock(kind, ["true"])
    if kind is ValueKind.VARIABLE:
        return ValueBlock(kind, ["x"])
    if kind is ValueKind.ARITHMETIC:
        return ValueBlock(kind, ["0", "0"], ARITHMETIC_OPERATORS[0])
    if kind is ValueKind.COMPARISON:
        return ValueBlock(kind, ["0", "0"], COMPARISON_OPERATORS[0])
    if kind is ValueKind.LOGICAL:
        return ValueBlock(kind, ["true", "true"], LOGICAL_OPERATORS[0])
    if kind is ValueKind.NOT:
        return ValueBlock(kind, ["true"])
    return ValueBlock(kind, ["2"])


def create_block(kind: BlockKind, blockId: int) -> Block:
    """Default block of the given kind (always valid)."""
    if kind is BlockKind.SET:
        return Block(kind, blockId, variableName="x", value=create_value(ValueKind.INTEGER))
    return Block(kind, blockId, operand=_DEFAULT_OPERANDS.get(kind, ""))


def _operand_text(node: ExpressionNode) -> str:
    if isinstance(node, LiteralNode):
        return format_value(node.value)
    if isinstance(node, VariableNode):
        return node.name
    raise BlockEditError(f"line {node.lineNumber}: operand expected")


def _value_from_expression(node: ExpressionNode) -> ValueBlock:
    if isinstance(node, LiteralNode):
        kind = ValueKind.BOOLEAN if isinstance(node.value, bool) else ValueKind.INTEGER
        return ValueBlock(kind, [format_value(node.value)])
    if isinstance(node, VariableNode):
        return ValueBlock(ValueKind.VARIABLE, [node.name])
    if isinstance(node, UnaryNode):
        return ValueBlock(ValueKind.NOT, [_operand_text(node.operand)])
    if isinstance(node, IsThereNode):
        return ValueBlock(ValueKind.IS_THERE, [_operand_text(node.argument)])
    if isinstance(node, BinaryNode):
        operands = [_operand_text(node.left), _operand_text(node.right)]
        return ValueBlock(_binary_kind(node.operator), operands, node.operator)
    raise BlockEditError(f"line {node.lineNumber}: unsupported expression")


def _binary_kind(operator: Operator) -> ValueKind:
    if operator in ARITHMETIC_OPERATORS:
        return ValueKind.ARITHMETIC
    if operator in COMPARISON_OPERATORS:
        return ValueKind.COMPARISON
    return ValueKind.LOGICAL


def blocks_from_statements(
    statements: Sequence[StatementNode], allocateId: Callable[[], int]
) -> list[Block]:
    """Convert parsed statements to blocks. Raises ``BlockEditError`` if not representable."""
    blocks = [_block_from_statement(statement, allocateId) for statement in statements]
    for block in blocks:
        if block.control_depth() > MAX_CONTROL_NESTING:
            raise BlockEditError(f"control blocks nested deeper than {MAX_CONTROL_NESTING}")
    return blocks


def _block_from_statement(statement: StatementNode, allocateId: Callable[[], int]) -> Block:
    blockId = allocateId()
    if isinstance(statement, SetNode):
        return Block(
            BlockKind.SET,
            blockId,
            variableName=statement.name,
            value=_value_from_expression(statement.expression),
        )
    if isinstance(statement, StepForwardNode):
        return Block(BlockKind.STEP_FORWARD, blockId, operand=_operand_text(statement.count))
    if isinstance(statement, TurnByNode):
        return Block(BlockKind.TURN_BY, blockId, operand=_operand_text(statement.count))
    if isinstance(statement, MineHereNode):
        return Block(BlockKind.MINE_HERE, blockId)
    if isinstance(statement, PrintNode):
        return Block(BlockKind.PRINT, blockId, operand=_operand_text(statement.expression))
    if isinstance(statement, IfNode):
        kind = BlockKind.IF if statement.elseBody is None else BlockKind.IF_ELSE
        block = Block(kind, blockId, operand=_operand_text(statement.condition))
        block.children = blocks_from_statements(statement.thenBody, allocateId)
        block.elseChildren = blocks_from_statements(statement.elseBody or [], allocateId)
        return block
    if isinstance(statement, WhileNode):
        block = Block(BlockKind.WHILE, blockId, operand=_operand_text(statement.condition))
        block.children = blocks_from_statements(statement.body, allocateId)
        return block
    raise BlockEditError(f"unsupported statement: {type(statement).__name__}")
