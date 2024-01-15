from typing import Type

from rply import ParserGenerator, Token

from ast_evaluator import ExecutionFrame
from code_generation.code_generator import CodeGenFrame
from terminal.base import Terminal


class DefArgument(Terminal):
    def __init__(self, name, wire="red", signal=None):
        self.arg_name = name
        self.wire = wire
        self.signal = signal

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : IDENTIFIER")
        def example_def(p: list[Token | Terminal]):
            return DefArgument(p[0])

        @gen.production(f"{this.name} : IDENTIFIER COLON WIRE_TYPE")
        def example_def(p: list[Token | Terminal]):
            return DefArgument(p[0], p[2].value)

        @gen.production(f"{this.name} : IDENTIFIER COLON SIGNAL")
        def example_def(p: list[Token | Terminal]):
            return DefArgument(p[0], "red", p[2].value)

    def evaluate(self, frame: 'ExecutionFrame'):
        super().evaluate(frame)

    def generate_opcodes(self, frame: CodeGenFrame):
        super().generate_opcodes(frame)


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

    def generate_opcodes(self, frame: CodeGenFrame):
        super().generate_opcodes(frame)


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

    def generate_opcodes(self, frame: CodeGenFrame):
        super().generate_opcodes(frame)
