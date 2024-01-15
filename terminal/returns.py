from typing import Type

from rply import ParserGenerator, Token

from ast_evaluator import ExecutionFrame
from code_generation.code_generator import CodeGenFrame
from code_generation.opcodes import Instruction, OpcodeKind
from terminal.expressoin import Expression
from terminal.base import Terminal


class Yield(Terminal):
    def __init__(self, value: 'Expression'):
        self.value = value

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : YIELD {Expression.name}")
        def example_def(p: tuple[Token, Expression]):
            return Yield(p[1])

    def evaluate(self, frame: 'ExecutionFrame'):
        output = self.value.evaluate(frame)
        frame.close_frame()
        return output

    def generate_opcodes(self, frame: CodeGenFrame):
        frame.open_frame()
        self.value.generate_opcodes(frame.current_frame)
        out_storage = frame.close_frame().return_storage

        frame.data.out_stack.dispose_all()
        if out_storage:
            frame.push_opcode(Instruction(
                OpcodeKind.mov,
                [
                    frame.data.out_stack.pop(),
                    out_storage
                ]
            ))


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

    def generate_opcodes(self, frame: CodeGenFrame):
        # TODO: stop function execution and return value
        frame.open_frame()
        self.value.generate_opcodes(frame.current_frame)
        out_storage = frame.close_frame().return_storage

        frame.data.out_stack.dispose_all()
        if out_storage:
            frame.push_opcode(Instruction(
                OpcodeKind.mov,
                [
                    frame.data.out_stack.pop(),
                    out_storage
                ]
            ))
