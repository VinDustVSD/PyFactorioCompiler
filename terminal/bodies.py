from typing import Optional, Type, TYPE_CHECKING

from rply import ParserGenerator, Token

from ast_evaluator import ExecutionFrame
from terminal.returns import Yield, Return
from terminal.base import Terminal
from terminal.expressoin import Expression
from code_generation.code_generator import CodeGenFrame
from terminal.assign import Assign
from terminal.compounds import ForStatement, IfStatement


class Body(Terminal):
    def __init__(self, item: Optional['Statement'], previous: Optional['Body'] = None):
        self.items: list['Statement'] = []
        self.items = previous.items if previous else []
        if item:
            self.items.append(item)

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} :")
        def empty_def(_):
            return Body(None)

        @gen.production(f"{this.name} : {this.name} {Statement.name}")
        def part_def(p):
            return Body(p[1], p[0])

    def evaluate(self, frame: 'ExecutionFrame'):
        for item in self.items:
            output = item.evaluate(frame)
            if item.name in [Yield.name, Return.name]:
                return output

    def generate_opcodes(self, frame: 'CodeGenFrame'):
        for item in self.items:
            frame.open_frame()
            item.generate_opcodes(frame.current_frame)
            frame.close_frame()


class Statement(Terminal):
    def __init__(self, value: Terminal):
        self.value = value

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : {Expression.name} SEMI_COLON")
        @gen.production(f"{this.name} : {Assign.name} SEMI_COLON")
        @gen.production(f"{this.name} : {Return.name} SEMI_COLON")
        @gen.production(f"{this.name} : {Yield.name} SEMI_COLON")
        @gen.production(f"{this.name} : {ForStatement.name}")
        @gen.production(f"{this.name} : {IfStatement.name}")
        def example_def(p: tuple[Terminal, Token]):
            return p[0]

    def evaluate(self, frame: 'ExecutionFrame'):
        self.value.evaluate(frame)
        return 0

    def generate_opcodes(self, frame: 'CodeGenFrame'):
        super().generate_opcodes(frame)
