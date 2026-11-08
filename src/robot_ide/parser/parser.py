"""Recursive-descent parser: tokenized lines -> AST. It never runs robot actions."""

from collections.abc import Sequence

from robot_ide.core.enums import Operator
from robot_ide.core.exceptions import MineScriptSyntaxError
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
from robot_ide.parser.tokenizer import SourceLine, Token, TokenKind, tokenize

_OPERATORS_BY_TEXT = {operator.value: operator for operator in Operator}


def parse_expression(tokens: Sequence[Token], lineNumber: int) -> ExpressionNode:
    """Parse a flat expression: operand | not operand | isThere operand | operand op operand."""
    if len(tokens) == 1:
        return _parse_operand(tokens[0], lineNumber)
    if len(tokens) == 2:
        head = tokens[0].text
        operand = _parse_operand(tokens[1], lineNumber)
        if head == "not":
            return UnaryNode(lineNumber, Operator.NOT, operand)
        if head == "isThere":
            return IsThereNode(lineNumber, operand)
        raise MineScriptSyntaxError(lineNumber, f"unexpected token {head!r} in expression")
    if len(tokens) == 3:
        middle = tokens[1]
        if middle.kind is not TokenKind.OPERATOR:
            raise MineScriptSyntaxError(lineNumber, f"operator expected, got {middle.text!r}")
        return BinaryNode(
            lineNumber,
            _OPERATORS_BY_TEXT[middle.text],
            _parse_operand(tokens[0], lineNumber),
            _parse_operand(tokens[2], lineNumber),
        )
    raise MineScriptSyntaxError(lineNumber, "invalid expression")


def _parse_operand(token: Token, lineNumber: int) -> ExpressionNode:
    if token.kind is TokenKind.INTEGER:
        return LiteralNode(lineNumber, int(token.text))
    if token.kind is TokenKind.BOOLEAN:
        return LiteralNode(lineNumber, token.text == "true")
    if token.kind is TokenKind.IDENTIFIER:
        return VariableNode(lineNumber, token.text)
    raise MineScriptSyntaxError(lineNumber, f"operand expected, got {token.text!r}")


class Parser:
    """Builds the statement tree from indentation-structured lines."""

    def __init__(self, sourceLines: Sequence[SourceLine]) -> None:
        self._lines = list(sourceLines)
        self._position = 0

    def parse_program(self) -> list[StatementNode]:
        """Parse all lines into top-level statements."""
        return self._parse_block(0)

    def _parse_block(self, indent: int) -> list[StatementNode]:
        statements: list[StatementNode] = []
        while self._position < len(self._lines):
            line = self._lines[self._position]
            if line.indent < indent:
                break
            if line.indent > indent:
                raise MineScriptSyntaxError(line.lineNumber, "unexpected indentation")
            statements.append(self._parse_statement(line))
        return statements

    def _parse_statement(self, line: SourceLine) -> StatementNode:
        head = line.tokens[0].text
        rest = line.tokens[1:]
        number = line.lineNumber
        if head == "set":
            return self._parse_set(line)
        if head == "step":
            self._expect_words(line, "step", "forward")
            self._position += 1
            return StepForwardNode(number, self._expression_after(line, 2))
        if head == "turn":
            self._expect_words(line, "turn", "by")
            self._position += 1
            return TurnByNode(number, self._expression_after(line, 2))
        if head == "mine":
            if [token.text for token in line.tokens] != ["mine", "here"]:
                raise MineScriptSyntaxError(number, "expected 'mine here'")
            self._position += 1
            return MineHereNode(number)
        if head == "print":
            self._position += 1
            return PrintNode(number, self._expression_after(line, 1))
        if head == "if":
            return self._parse_if(line)
        if head == "while":
            condition = parse_expression(rest, number)
            self._position += 1
            return WhileNode(number, condition, self._parse_child_block(line))
        if head == "else":
            raise MineScriptSyntaxError(number, "'else' without matching 'if'")
        raise MineScriptSyntaxError(number, f"unknown statement {head!r}")

    def _parse_set(self, line: SourceLine) -> SetNode:
        tokens = line.tokens
        if len(tokens) < 4 or tokens[2].text != "to":
            raise MineScriptSyntaxError(line.lineNumber, "expected 'set <name> to <expression>'")
        if tokens[1].kind is not TokenKind.IDENTIFIER:
            raise MineScriptSyntaxError(
                line.lineNumber, f"invalid variable name {tokens[1].text!r}"
            )
        self._position += 1
        return SetNode(line.lineNumber, tokens[1].text, self._expression_after(line, 3))

    def _parse_if(self, line: SourceLine) -> IfNode:
        condition = parse_expression(line.tokens[1:], line.lineNumber)
        self._position += 1
        thenBody = self._parse_child_block(line)
        if self._position < len(self._lines):
            candidate = self._lines[self._position]
            if candidate.indent == line.indent and candidate.tokens[0].text == "else":
                if len(candidate.tokens) != 1:
                    raise MineScriptSyntaxError(candidate.lineNumber, "'else' takes no arguments")
                self._position += 1
                elseBody = self._parse_child_block(candidate)
                return IfNode(line.lineNumber, condition, thenBody, elseBody, candidate.lineNumber)
        return IfNode(line.lineNumber, condition, thenBody)

    def _parse_child_block(self, header: SourceLine) -> list[StatementNode]:
        if self._position >= len(self._lines):
            raise MineScriptSyntaxError(header.lineNumber, "indented block expected")
        childIndent = self._lines[self._position].indent
        if childIndent <= header.indent:
            raise MineScriptSyntaxError(header.lineNumber, "indented block expected")
        return self._parse_block(childIndent)

    @staticmethod
    def _expect_words(line: SourceLine, first: str, second: str) -> None:
        if len(line.tokens) < 3 or line.tokens[1].text != second:
            raise MineScriptSyntaxError(line.lineNumber, f"expected '{first} {second} <value>'")

    @staticmethod
    def _expression_after(line: SourceLine, skip: int) -> ExpressionNode:
        return parse_expression(line.tokens[skip:], line.lineNumber)


def parse_source(programLines: Sequence[str]) -> list[StatementNode]:
    """Tokenize and parse program lines into an AST."""
    return Parser(tokenize(programLines)).parse_program()
