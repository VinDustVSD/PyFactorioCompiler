from typing import Type

from rply import Token, ParserGenerator

from ast_evaluator import ExecutionFrame
from code_generation.code_generator import CodeGenFrame
from code_generation.opcodes import Instruction, OpcodeKind
from code_generation.stacks import Const
from terminal.expressoin import Expression
from terminal.base import Terminal, Variable
from tokens import TokenKind


class Assign(Terminal):
    def __init__(self, name: Token, value: 'Expression'):
        self.a_name = name.value
        self.value = value

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : IDENTIFIER ASSIGN {Expression.name}")
        def example_def(p: tuple[Token, Token, Expression]):
            return Assign(p[0], p[2])

        @gen.production(f"{this.name} : IDENTIFIER ASSIGN_SUM {Expression.name}")
        @gen.production(f"{this.name} : IDENTIFIER ASSIGN_SUB {Expression.name}")
        @gen.production(f"{this.name} : IDENTIFIER ASSIGN_MUL {Expression.name}")
        @gen.production(f"{this.name} : IDENTIFIER ASSIGN_DIV {Expression.name}")
        @gen.production(f"{this.name} : IDENTIFIER ASSIGN_POW {Expression.name}")
        def example_def(p: tuple[Token, Token, Expression]):
            operator = {
                TokenKind.ASSIGN_SUM.name: Token(TokenKind.OP_SUM.name, "+", p[1].source_pos),
                TokenKind.ASSIGN_SUB.name: Token(TokenKind.OP_SUB.name, "-", p[1].source_pos),
                TokenKind.ASSIGN_MUL.name: Token(TokenKind.OP_MUL.name, "*", p[1].source_pos),
                TokenKind.ASSIGN_DIV.name: Token(TokenKind.OP_DIV.name, "/", p[1].source_pos),
                TokenKind.ASSIGN_POW.name: Token(TokenKind.OP_POW.name, "**", p[1].source_pos),
            }[p[1].name]
            expression = Expression(Variable(p[0].value, None), operator, p[2])
            return Assign(p[0], expression)

    def evaluate(self, frame: 'ExecutionFrame'):
        value = self.value.evaluate(frame)
        frame.set_local(self.a_name, value)

    def generate_opcodes(self, frame: CodeGenFrame):
        self.value.generate_opcodes(frame.open_frame())
        value_frame = frame.close_frame()
        if self.a_name in frame.data.locals:
            reg = frame.get(self.a_name).n_storage

        else:
            reg = frame.reg_stack.pop()

        if isinstance(reg, Const):
            reg = frame.reg_stack.pop()
            frame.push_opcode(Instruction(
                OpcodeKind.mov,
                [reg, value_frame.return_storage]
            ))

        # SemanticAnalyzer must check if assign expression returns value, right?
        var = Variable(self.a_name, reg)
        frame.set_local(self.a_name, var)
