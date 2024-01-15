from typing import Type, TYPE_CHECKING

from rply import ParserGenerator, Token

if TYPE_CHECKING:
    from ast_evaluator import ExecutionFrame
    from code_generation.code_generator import CodeGenFrame

from code_generation.stacks import Const


class Terminal:
    name = None

    @staticmethod
    def gen_productions(this_class: Type['Terminal'], gen: ParserGenerator):
        pass

    def evaluate(self, frame: 'ExecutionFrame'):
        raise NotImplementedError(f"Evaluating not implemented in {self.__class__}.")

    def generate_opcodes(self, frame: 'CodeGenFrame'):
        raise NotImplementedError(f"Opcode generation not implemented in {self.__class__}.")


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

    def generate_opcodes(self, frame: 'CodeGenFrame'):
        super().generate_opcodes(frame)


class NumberLiteral(Terminal):
    def __init__(self, value: int | float):
        self.value = value

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : NUMBER_INT")
        def example_def(p: tuple[Token]):
            return NumberLiteral(int(p[0].value))

        @gen.production(f"{this.name} : NUMBER_FLOAT")
        @gen.production(f"{this.name} : NUMBER_SCI_FORM")
        def example_def(p: tuple[Token]):
            return NumberLiteral(float(p[0].value))

    def evaluate(self, frame: 'ExecutionFrame'):
        return self.value

    def generate_opcodes(self, frame: 'CodeGenFrame'):
        frame.return_storage = Const(self.value)


class Variable(Terminal):
    def __init__(self, name, storage):
        self.a_name = name
        self.n_storage_ = storage
        self.n_on_get_storage = lambda this: this.n_storage_

    @property
    def n_storage(self):
        return self.n_on_get_storage(self)

    def evaluate(self, frame: 'ExecutionFrame'):
        return frame.locals[self.a_name]

    def generate_opcodes(self, frame: 'CodeGenFrame'):
        if self.a_name in frame.data.locals:
            self.n_storage_ = frame.get(self.a_name).n_storage

        frame.return_storage = self.n_storage_
