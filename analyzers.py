from typing import Type

from rply import ParserGenerator, LexerGenerator
from rply.lexer import LexerStream, Lexer as _Lexer

from terminal import all_terminals, Terminal
from tokens import TokenKind


class Lexer(_Lexer):
    def __init__(self):
        gen = LexerGenerator()
        for token in TokenKind:
            for pattern in token.value:
                gen.add(token.name, pattern)
        gen.ignore(r"\s")

        self._lexer = gen.build()

    def lex(self, s):
        return self._lexer.lex(s)


class Parser:
    def __init__(self):
        gen = ParserGenerator(
            [i.name for i in TokenKind],
            precedence=[
                ("left", [TokenKind.OP_SUM.name, TokenKind.OP_SUB.name]),
                ("left", [TokenKind.OP_MUL.name, TokenKind.OP_DIV.name]),
                ("right", [TokenKind.OP_POW.name]),
            ]
        )

        self.terminals = all_terminals
        self._gen_productions(gen, self.terminals)
        self._parser = gen.build()

    @staticmethod
    def _gen_productions(gen: ParserGenerator, terminals: dict[str, Type[Terminal]]):
        for terminal in terminals.values():
            terminal.gen_productions(terminal, gen)

    def parse(self, tokenizer: LexerStream, state=None):
        return self._parser.parse(tokenizer, state)


class SemanticAnalyzer:
    def __init__(self):
        pass
