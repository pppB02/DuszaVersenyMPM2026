"""Block data models. The block tree is the single source of truth while editing."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum

from robot_ide.core.enums import Operator


class BlockKind(Enum):
    """Statement blocks."""

    SET = "SET"
    STEP_FORWARD = "STEP_FORWARD"
    TURN_BY = "TURN_BY"
    MINE_HERE = "MINE_HERE"
    PRINT = "PRINT"
    IF = "IF"
    IF_ELSE = "IF_ELSE"
    WHILE = "WHILE"

    @property
    def is_control(self) -> bool:
        """True for blocks that can contain other blocks."""
        return self in (BlockKind.IF, BlockKind.IF_ELSE, BlockKind.WHILE)

    @property
    def uses_operand(self) -> bool:
        """True if the block has one operand field (count, condition or printed value)."""
        return self in (
            BlockKind.STEP_FORWARD,
            BlockKind.TURN_BY,
            BlockKind.PRINT,
            BlockKind.IF,
            BlockKind.IF_ELSE,
            BlockKind.WHILE,
        )


class ValueKind(Enum):
    """Right-hand-side value blocks; they only exist inside a SET block."""

    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    VARIABLE = "VARIABLE"
    ARITHMETIC = "ARITHMETIC"
    COMPARISON = "COMPARISON"
    LOGICAL = "LOGICAL"
    NOT = "NOT"
    IS_THERE = "IS_THERE"

    @property
    def operand_count(self) -> int:
        """Number of operand fields."""
        return 2 if self in (ValueKind.ARITHMETIC, ValueKind.COMPARISON, ValueKind.LOGICAL) else 1


class Branch(Enum):
    """Which child list of a control block."""

    MAIN = "MAIN"
    ELSE = "ELSE"


ARITHMETIC_OPERATORS = (Operator.ADD, Operator.SUBTRACT, Operator.MULTIPLY)
COMPARISON_OPERATORS = (
    Operator.LESS,
    Operator.LESS_EQUAL,
    Operator.GREATER,
    Operator.GREATER_EQUAL,
    Operator.EQUAL,
    Operator.NOT_EQUAL,
)
LOGICAL_OPERATORS = (Operator.AND, Operator.OR)
OPERATORS_BY_VALUE_KIND = {
    ValueKind.ARITHMETIC: ARITHMETIC_OPERATORS,
    ValueKind.COMPARISON: COMPARISON_OPERATORS,
    ValueKind.LOGICAL: LOGICAL_OPERATORS,
}


@dataclass
class ValueBlock:
    """Value of a SET block. Operands are plain text: a number, true/false or a variable."""

    kind: ValueKind
    operands: list[str]
    operator: Operator | None = None


@dataclass
class Block:
    """One statement block."""

    kind: BlockKind
    blockId: int
    variableName: str = ""
    operand: str = ""
    value: ValueBlock | None = None
    children: list["Block"] = field(default_factory=list)
    elseChildren: list["Block"] = field(default_factory=list)

    def branch_blocks(self, branch: Branch) -> list["Block"]:
        """Child list of the given branch."""
        return self.children if branch is Branch.MAIN else self.elseChildren

    def walk(self) -> Iterator["Block"]:
        """This block and all descendants, depth first."""
        yield self
        for child in (*self.children, *self.elseChildren):
            yield from child.walk()

    def control_depth(self) -> int:
        """Control-block nesting depth of this subtree, counting this block."""
        nested = (*self.children, *self.elseChildren)
        deepest = max((child.control_depth() for child in nested), default=0)
        return deepest + (1 if self.kind.is_control else 0)
