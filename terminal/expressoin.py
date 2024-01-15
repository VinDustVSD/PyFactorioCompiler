from typing import Type, Union

from rply import Token, ParserGenerator

from ast_evaluator import ExecutionFrame
from code_generation.code_generator import CodeGenFrame
from code_generation.opcodes import OpcodeKind, Instruction
from code_generation.stacks import Register, MemoryCell
from terminal.base import Terminal, NumberLiteral, Variable
from tokens import TokenKind


class UnaryExpr(Terminal):
    def __init__(self, operator: Token, identifier: 'str', mode=0):
        self.operator = operator
        self.identifier = identifier
        self.mode = mode

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : IDENTIFIER INCREMENT")
        @gen.production(f"{this.name} : IDENTIFIER DECREMENT")
        def expr_unary(p):
            return UnaryExpr(p[1], p[0].value, 0)

        @gen.production(f"{this.name} : INCREMENT IDENTIFIER")
        @gen.production(f"{this.name} : DECREMENT IDENTIFIER")
        def expr_unary(p):
            return UnaryExpr(p[0], p[1].value, 1)

    def evaluate(self, frame: 'ExecutionFrame'):
        value = frame.locals[self.identifier] if self.mode else None
        if self.operator.name == TokenKind.INCREMENT.name:
            frame.locals[self.identifier] += 1

        elif self.operator.name == TokenKind.DECREMENT.name:
            frame.locals[self.identifier] -= 1

        if not value:
            value = frame.locals[self.identifier]

        return value

    def generate_opcodes(self, frame: CodeGenFrame):
        operator = OpcodeKind.inc if self.operator.name == TokenKind.INCREMENT.name else OpcodeKind.dec
        frame.push_opcode(Instruction(
            operator,
            [frame.get(self.identifier).n_storage]
        ))


class Expression(Terminal):
    def __init__(self, left: Union['Expression', 'Terminal'], operator: Token, right: Union['Expression', 'Terminal']):
        self.left = left
        self.operator = operator
        self.right = right

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : {NumberLiteral.name}")
        @gen.production(f"{this.name} : {UnaryExpr.name}")
        def expr_number(p: list[Token | Terminal]):
            return p[0]

        @gen.production(f"{this.name} : IDENTIFIER")
        def expr_number(p: list[Token | Terminal]):
            return Variable(p[0].value, None)

        @gen.production(f"{this.name} : {this.name} OP_CMP_EQ {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_CMP_NE {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_CMP_GE {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_CMP_LE {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_CMP_GT {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_CMP_LT {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_SUM {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_SUB {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_MUL {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_DIV {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_MOD {this.name}")
        @gen.production(f"{this.name} : {this.name} OP_POW {this.name}")
        def expr_binary(p):
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
            "OP_CMP_EQ": lambda a, b: a == b,
            "OP_CMP_NE": lambda a, b: a != b,
            "OP_CMP_GE": lambda a, b: a >= b,
            "OP_CMP_LE": lambda a, b: a <= b,
            "OP_CMP_GT": lambda a, b: a > b,
            "OP_CMP_LT": lambda a, b: a < b,

        }

        operator = operations.get(self.operator.name)
        if not operator:
            raise ValueError(f"Evaluating invalid operator token: '{self.operator}'")

        return operator(self.left.evaluate(frame), self.right.evaluate(frame))

    def generate_opcodes(self, frame: CodeGenFrame):
        if isinstance(self.left, Variable) and self.left.a_name in frame.data.locals:
            self.left = frame.get(self.left.a_name)

        if isinstance(self.right, Variable) and self.right.a_name in frame.data.locals:
            self.right = frame.get(self.right.a_name)

        frame.open_frame()
        self.left.generate_opcodes(frame.current_frame)
        left_reg_or_val = frame.close_frame().return_storage

        frame.open_frame()
        self.right.generate_opcodes(frame.current_frame)
        right_reg_or_val = frame.close_frame().return_storage

        if (
            (isinstance(left_reg_or_val, Register) or isinstance(left_reg_or_val, MemoryCell)) and
            left_reg_or_val not in frame.data.registers_in_locals
        ):
            output_register = left_reg_or_val
            if isinstance(right_reg_or_val, Register) and right_reg_or_val not in frame.data.registers_in_locals:
                right_reg_or_val.dispose()

        elif (
            (isinstance(right_reg_or_val, Register) or isinstance(right_reg_or_val, MemoryCell)) and
            right_reg_or_val not in frame.data.registers_in_locals
        ):
            output_register = right_reg_or_val

        else:
            output_register = frame.reg_stack.pop()

        opcode = Instruction(
            {
                "OP_SUM": OpcodeKind.add,
                "OP_SUB": OpcodeKind.sub,
                "OP_MUL": OpcodeKind.mul,
                "OP_DIV": OpcodeKind.div,
                "OP_MOD": OpcodeKind.mod,
                "OP_POW": OpcodeKind.pow,
            }[self.operator.name],
            [
                output_register,
                left_reg_or_val,
                right_reg_or_val,
            ]
        )

        frame.return_storage = output_register
        frame.push_opcode(opcode)
