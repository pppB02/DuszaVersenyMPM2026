"""Splits MineScript source into indented, tokenized lines."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from robot_ide.core.constants import KEYWORDS, MAX_NUMBER, MIN_NUMBER
from robot_ide.core.exceptions import MineScriptSyntaxError
from robot_ide.parser.syntax_validator import is_valid_identifier

_OPERATOR_TEXTS = frozenset({"+", "-", "*", "<", "<=", ">", ">=", "=", "<>", "and", "or"})
_BOOLEAN_TEXTS = frozenset({"true", "false"})


class TokenKind(Enum):
    """Token categories."""

    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    OPERATOR = "OPERATOR"
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"


@dataclass(frozen=True)
class Token:
    """One space-separated word."""

    kind: TokenKind
    text: str
    lineNumber: int


@dataclass(frozen=True)
class SourceLine:
    """A non-blank program line: its number, indent (in spaces) and tokens."""

    lineNumber: int
    indent: int
    tokens: tuple[Token, ...]


def _classify(text: str, lineNumber: int) -> Token:
    if text in _BOOLEAN_TEXTS:
        return Token(TokenKind.BOOLEAN, text, lineNumber)
    if text in _OPERATOR_TEXTS:
        return Token(TokenKind.OPERATOR, text, lineNumber)
    if text in KEYWORDS:
        return Token(TokenKind.KEYWORD, text, lineNumber)
    if text.isascii() and text.isdigit():
        if not MIN_NUMBER <= int(text) <= MAX_NUMBER:
            raise MineScriptSyntaxError(lineNumber, f"number out of range 0..100: {text}")
        return Token(TokenKind.INTEGER, text, lineNumber)
    if is_valid_identifier(text):
        return Token(TokenKind.IDENTIFIER, text, lineNumber)
    raise MineScriptSyntaxError(lineNumber, f"invalid token: {text!r}")


def tokenize(programLines: Sequence[str]) -> list[SourceLine]:
    """Tokenize program lines. Blank lines are skipped but still count for numbering."""
    result: list[SourceLine] = []
    for index, rawLine in enumerate(programLines):
        lineNumber = index + 1
        stripped = rawLine.strip()
        if not stripped:
            continue
        leading = rawLine[: len(rawLine) - len(rawLine.lstrip())]
        if "\t" in leading:
            raise MineScriptSyntaxError(lineNumber, "tab is not allowed for indentation")
        tokens = tuple(_classify(word, lineNumber) for word in stripped.split())
        result.append(SourceLine(lineNumber, len(leading), tokens))
    return result
