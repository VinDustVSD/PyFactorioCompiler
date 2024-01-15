from typing import Type, TYPE_CHECKING, Optional

from rply import ParserGenerator

from ast_evaluator import ExecutionFrame
from code_generation.code_generator import CodeGenFrame
from exceptions import IdentifierError
from terminal.base import Terminal

if TYPE_CHECKING:
    from terminal.function import Function


class Program(Terminal):
    def __init__(self, function: 'Function', previous: Optional['Program']):
        self.n_functions: dict[str, 'Function'] = {}
        if previous:
            self.n_functions = previous.n_functions

        if function.a_name in self.n_functions:
            raise IdentifierError(f"Function '{function.a_name}' already exists!")

        self.n_functions[function.a_name] = function
        self.n_entry_point_name = "Main"
        self.functions = list(self.n_functions.values())

        if self.n_entry_point_name not in self.n_functions:
            raise NotImplementedError(f"No entry_point (function called '{self.n_entry_point_name}').")

        self.n_functions[self.n_entry_point_name].n_is_entry_point = True

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : ")
        def example_def(_):
            return

        @gen.production(f"{this.name} : {this.name} function")
        def example_def(p: tuple['Program', 'Function']):
            return Program(p[1], p[0])

    @property
    def entry_point(self):
        return self.n_functions[self.n_entry_point_name]

    def evaluate(self, frame: 'ExecutionFrame'):
        return self.entry_point.evaluate(frame)

    def generate_opcodes(self, frame: CodeGenFrame):
        super().generate_opcodes(frame)
