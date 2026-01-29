from __future__ import annotations

from funpayhub.lib.hub.text_formatters.category import CategoriesQuery


__all__ = ['parse_categories_query']


import re
from typing import Iterator


TOKEN_REGEX = re.compile(
    r"""
    (?P<WS>\s+)|
    (?P<ID>[a-zA-Z0-9\-_.:]+)|
    (?P<AND>&)|
    (?P<OR>\|)|
    (?P<NOT>!)|
    (?P<LPAREN>\()|
    (?P<RPAREN>\))
    """,
    re.VERBOSE,
)


class Token:
    def __init__(self, kind: str, value: str) -> None:
        self.kind = kind
        self.value = value

    def __repr__(self) -> str:
        return f'Token({self.kind!r}, {self.value!r})'


def tokenize(expr: str) -> Iterator[Token]:
    pos = 0
    while pos < len(expr):
        m = TOKEN_REGEX.match(expr, pos)
        if not m:
            raise SyntaxError(f'Invalid character at position {pos}: {expr[pos]!r}')
        kind = m.lastgroup
        value = m.group(kind)
        pos = m.end()

        if kind != 'WS':
            yield Token(kind, value)


class CategoryIDQuery(CategoriesQuery):
    def __init__(self, id: str) -> None:
        self.id = id

    def __call__(self, formatter, registry) -> bool:
        cat = registry._categories.get(self.id)
        if not cat:
            return False
        return cat.contains(formatter, registry)


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected=None) -> Token:
        token = self.peek()
        if not token:
            raise SyntaxError('Unexpected end of expression')

        if expected and token.kind != expected:
            raise SyntaxError(f'Expected {expected}, got {token.kind}')

        self.pos += 1
        return token

    def parse(self) -> CategoriesQuery:
        result = self.parse_or()
        if self.peek():
            raise SyntaxError(f'Unexpected token: {self.peek()}')
        return result

    def parse_or(self) -> CategoriesQuery:
        node = self.parse_and()
        while self.peek() and self.peek().kind == 'OR':
            self.consume('OR')
            rhs = self.parse_and()
            node = node.or_(rhs)
        return node

    def parse_and(self) -> CategoriesQuery:
        node = self.parse_not()
        while self.peek() and self.peek().kind == 'AND':
            self.consume('AND')
            rhs = self.parse_not()
            node = node.and_(rhs)
        return node

    def parse_not(self) -> CategoriesQuery:
        if self.peek() and self.peek().kind == 'NOT':
            self.consume('NOT')
            return self.parse_not().invert()
        return self.parse_primary()

    def parse_primary(self) -> CategoriesQuery:
        token = self.peek()
        if not token:
            raise SyntaxError('Unexpected end of input')

        if token.kind == 'ID':
            self.consume('ID')
            return CategoryIDQuery(token.value)

        if token.kind == 'LPAREN':
            self.consume('LPAREN')
            node = self.parse_or()
            self.consume('RPAREN')
            return node

        raise SyntaxError(f'Unexpected token: {token}')


def parse_categories_query(expr: str) -> CategoriesQuery:
    tokens = list(tokenize(expr))
    parser = Parser(tokens)
    return parser.parse()
