from typing import Type, Optional, TYPE_CHECKING

from rply import ParserGenerator, Token

if TYPE_CHECKING:
    from ast_evaluator import ExecutionFrame


class Terminal:
    name = None

    @staticmethod
    def gen_productions(this_class: Type['Terminal'], gen: ParserGenerator):
        pass

    def evaluate(self, frame: 'ExecutionFrame'):
        raise NotImplementedError(f"Evaluating not implemented in {self.__class__}.")


class Example(Terminal):
    def __init__(self):
        pass

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : ")
        def example_def(_: list[Token | Terminal]):
            return this()

    def evaluate(self, frame: 'ExecutionFrame'):
        super().evaluate(frame)


class Program(Terminal):
    def __init__(self, function: 'Function'):
        # TODO: Define multiple functions and call it
        self.n_functions = {function.a_name: function}
        self.n_entry_point_name = "Main"
        self.functions = list(self.n_functions.values())

        if self.n_entry_point_name not in self.n_functions:
            raise NotImplementedError(f"No entry_point (function called '{self.n_entry_point_name}').")

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : {Function.name}")
        def example_def(p: tuple[Function]):
            return Program(p[0])

    @property
    def entry_point(self):
        return self.n_functions[self.n_entry_point_name]

    def evaluate(self, frame: 'ExecutionFrame'):
        return self.entry_point.evaluate(frame)


class DefArgument(Terminal):
    def __init__(self, name, wire="red"):
        self.arg_name = name
        self.wire = wire

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : IDENTIFIER")
        def example_def(p: list[Token | Terminal]):
            return DefArgument(p[0])

        @gen.production(f"{this.name} : IDENTIFIER COLON WIRE_TYPE")
        def example_def(p: list[Token | Terminal]):
            return DefArgument(p[0], p[2].value)

    def evaluate(self, frame: 'ExecutionFrame'):
        super().evaluate(frame)


class DefArgs(Terminal):
    def __init__(self, items: list[DefArgument]):
        self.items = items

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} :")
        def empty_def(_):
            return

        @gen.production(f"{this.name} : {DefArgument.name} {SepCollectorDefArgs.name}")
        def part_def(p: list[DefArgs | DefArgument]):
            items = []
            if p[0]:
                items.append(p[0])
                if p[1]:
                    items += p[1].items

            return DefArgs(items)

    def evaluate(self, frame: 'ExecutionFrame'):
        super().evaluate(frame)


class SepCollectorDefArgs(Terminal):
    def __init__(self, item: DefArgument, previous: 'SepCollectorDefArgs'):
        self.items = None
        self.items = previous.items if previous else []
        self.items.append(item)

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} :")
        def empty_def(_):
            return

        @gen.production(f"{this.name} : {this.name} COMMA {DefArgument.name}")
        def part_def(p: list[SepCollectorDefArgs | DefArgument]):
            return SepCollectorDefArgs(p[2], p[0])

    def evaluate(self, frame: 'ExecutionFrame'):
        super().evaluate(frame)


class Function(Terminal):
    def __init__(self, name: Token, args: DefArgs, body: 'Body'):
        self.a_name: str = name.value
        self.args = args
        self.body = body

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : FUNC_DEF IDENTIFIER LPAREN {DefArgs.name} RPAREN LBRACE {Body.name} RBRACE")
        def example_def(p: tuple[Token, Token, Token, DefArgs, Token, Token, Body, Token]):
            return Function(p[1], p[3], p[6])

    def evaluate(self, frame: 'ExecutionFrame'):
        frame.new_frame()
        return self.body.evaluate(frame)


class Body(Terminal):
    def __init__(self, item: 'Statement', previous: Optional['Body']):
        self.items: list['Statement'] = []
        self.items = previous.items if previous else []
        self.items.append(item)

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} :")
        def empty_def(_):
            return

        @gen.production(f"{this.name} : {this.name} {Statement.name}")
        def part_def(p):
            return Body(p[1], p[0])

    def evaluate(self, frame: 'ExecutionFrame'):
        for item in self.items:
            output = item.evaluate(frame)
            if item.name == Return.name:
                return output


class Statement(Terminal):
    def __init__(self, value: Terminal):
        self.value = value

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : {Expression.name} SEMI_COLON")
        @gen.production(f"{this.name} : {Assign.name} SEMI_COLON")
        @gen.production(f"{this.name} : {Return.name} SEMI_COLON")
        def example_def(p: tuple[Terminal, Token]):
            return p[0]

    def evaluate(self, frame: 'ExecutionFrame'):
        self.value.evaluate(frame)
        return 0


class Return(Terminal):
    def __init__(self, value: 'Expression'):
        self.value = value

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : RETURN {Expression.name}")
        def example_def(p: tuple[Token, Expression]):
            return Return(p[1])

    def evaluate(self, frame: 'ExecutionFrame'):
        output = self.value.evaluate(frame)
        frame.close_frame()
        return output


class Assign(Terminal):
    def __init__(self, name: Token, value: 'Expression'):
        self.a_name = name
        self.value = value

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : IDENTIFIER ASSIGN {Expression.name}")
        def example_def(p: tuple[Token, Token, Expression]):
            return Assign(p[0], p[2])

    def evaluate(self, frame: 'ExecutionFrame'):
        value = self.value.evaluate(frame)
        frame.set_local(self.a_name.value, value)


class Expression(Terminal):
    def __init__(self, left: 'Expression', operator: Token, right: 'Expression'):
        self.left = left
        self.operator = operator
        self.right = right

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : {NumberLiteral.name}")
        def expr_number(p: list[Token | Terminal]):
            return p[0]

        @gen.production(f"{this.name} : {this.name} OP_SUM {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_SUB {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_MUL {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_DIV {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_POW {this.name}")
        def expr_operator(p):
            return Expression(*p)

        @gen.production(f"{this.name} : LPAREN {this.name} RPAREN")
        def expr_paren(p):
            return p[1]

    def evaluate(self, frame: 'ExecutionFrame'):
        operations = {
            "OP_SUM": lambda a, b: a + b,
            "OP_SUB": lambda a, b: a - b,
            "OP_MUL": lambda a, b: a * b,
            "OP_DIV": lambda a, b: a / b,
            "OP_POW": lambda a, b: a ** b,
        }

        operator = operations.get(self.operator.name)
        if not operator:
            raise ValueError(f"Evaluating invalid operator token: '{self.operator}'")

        return operator(self.left.evaluate(frame), self.right.evaluate(frame))


class NumberLiteral(Terminal):
    def __init__(self, token: Token):
        self.token = token

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : NUMBER")
        def example_def(p: list[Token | Terminal]):
            return NumberLiteral(p[0])

    def evaluate(self, frame: 'ExecutionFrame'):
        return int(self.token.value)


all_terminals: dict[str, Type[Terminal]] = {}
_locals = locals().copy()


def get_terminal_name(term: Type['Terminal']):
    name = ""
    for char in term.__name__:
        if char.isupper() and len(name) > 0 and name[-1].islower():
            char = "_" + char
        name += char

    return name.lower()


def _find_terminals_and_init():
    for key in _locals:
        if (
                key.startswith("_") or
                type(_locals[key]) != type(type) or
                not issubclass(_locals[key], Terminal) or
                key in ["Terminal", "Example"]
        ):
            continue

        term: Type[Terminal] = _locals[key]
        term.name = get_terminal_name(term)
        all_terminals[term.name] = term


_find_terminals_and_init()
