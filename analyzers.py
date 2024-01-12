from typing import Type

from rply import ParserGenerator, LexerGenerator, Token, ParsingError
from rply.lexer import LexerStream, Lexer as _Lexer

from exceptions import ParsingException
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
        self._parser.error_handler = self._error_handler
        self._last_parsing_tokens: LexerStream | None = None

    @staticmethod
    def _gen_productions(gen: ParserGenerator, terminals: dict[str, Type[Terminal]]):
        for terminal in terminals.values():
            terminal.gen_productions(terminal, gen)

    def parse(self, tokenizer: LexerStream, state=None):
        self._last_parsing_tokens = tokenizer
        from rply.token import Token

        lookahead = None
        lookahead_stack = []

        state_stack = [0]
        sym_stack = [Token("$end", "$end")]

        current_state = 0
        while True:
            if self._parser.lr_table.default_reductions[current_state]:
                t = self._parser.lr_table.default_reductions[current_state]
                current_state = self._reduce_production(
                    t, sym_stack, state_stack, state
                )
                continue

            if lookahead is None:
                if lookahead_stack:
                    lookahead = lookahead_stack.pop()
                else:
                    try:
                        lookahead = next(tokenizer)
                    except StopIteration:
                        lookahead = None

                if lookahead is None:
                    lookahead = Token("$end", "$end")

            l_type = lookahead.gettokentype()
            if l_type in self._parser.lr_table.lr_action[current_state]:
                t = self._parser.lr_table.lr_action[current_state][l_type]
                if t > 0:
                    state_stack.append(t)
                    current_state = t
                    sym_stack.append(lookahead)
                    lookahead = None
                    continue
                elif t < 0:
                    current_state = self._reduce_production(
                        t, sym_stack, state_stack, state
                    )
                    continue
                else:
                    n = sym_stack[-1]
                    return n
            else:
                # TODO: actual error handling here
                if self._parser.error_handler is not None:
                    if state is None:
                        self._parser.error_handler(current_state, lookahead)
                    else:
                        self._parser.error_handler(current_state, state, lookahead)
                    raise AssertionError("For now, error_handler must raise.")
                else:
                    raise ParsingError(None, lookahead.getsourcepos())

    def _reduce_production(self, t, sym_stack, state_stack, state):
        # reduce a symbol on the stack and emit a production
        p = self._parser.lr_table.grammar.productions[-t]
        pname = p.name
        p_len = p.getlength()
        start = len(sym_stack) + (-p_len - 1)
        assert start >= 0
        targ = sym_stack[start + 1:]
        start = len(sym_stack) + (-p_len)
        assert start >= 0
        del sym_stack[start:]
        del state_stack[start:]
        if state is None:
            value = p.func(targ)
        else:
            value = p.func(state, targ)
        sym_stack.append(value)
        current_state = self._parser.lr_table.lr_goto[state_stack[-1]][pname]
        state_stack.append(current_state)
        return current_state

    def _error_handler(self, current_state: int, state, lookahead: 'Token' = None):
        if not lookahead:
            lookahead = state
            state = None

        err_text = f"Excepted {list(self._parser.lr_table.lr_action[current_state].keys())},\n" \
                   f"got {lookahead.name} " \
                   f"at {lookahead.source_pos}"
        err_text += '\n"'
        err_text += self._last_parsing_tokens.s.split("\n")[lookahead.source_pos.lineno - 1]
        err_text += f'"\n{" " * lookahead.source_pos.colno}{"^" * len(lookahead.value)}'
        raise ParsingException(err_text)


class SemanticAnalyzer:
    def __init__(self):
        pass
