"""Static checks shared by the tokenizer, parser and block editor."""

import re
from collections.abc import Sequence

from robot_ide.core.constants import KEYWORDS
from robot_ide.parser.ast_nodes import IfNode, StatementNode, WhileNode

_IDENTIFIER_PATTERN = re.compile(r"[^\W\d]\w*")


def is_valid_identifier(name: str) -> bool:
    """True if ``name`` is a legal variable name (not a keyword, not starting with a digit)."""
    return _IDENTIFIER_PATTERN.fullmatch(name) is not None and name not in KEYWORDS


def control_depth(statements: Sequence[StatementNode]) -> int:
    """Deepest nesting of control blocks (``if``/``while``) in a statement list."""
    deepest = 0
    for statement in statements:
        if isinstance(statement, IfNode):
            children = list(statement.thenBody) + list(statement.elseBody or [])
            deepest = max(deepest, 1 + control_depth(children))
        elif isinstance(statement, WhileNode):
            deepest = max(deepest, 1 + control_depth(statement.body))
    return deepest
