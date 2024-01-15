from typing import Type, Union, TYPE_CHECKING

from rply import ParserGenerator, Token

from terminal.base import Terminal
from code_generation.opcodes import Label, OpcodeKind, Instruction
from code_generation.stacks import Const

if TYPE_CHECKING:
    from ast_evaluator import ExecutionFrame
    from code_generation.code_generator import CodeGenFrame
    from terminal.expressoin import Expression
    from terminal.bodies import Body
    from terminal.assign import Assign


class Condition(Terminal):
    def __init__(self, expr: 'Expression'):
        self.expr = expr

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : expression")
        def example_def(p: tuple['Expression']):
            return Condition(p[0])

    def evaluate(self, frame: 'ExecutionFrame'):
        return self.expr.evaluate(frame)

    def generate_opcodes(self, frame: 'CodeGenFrame', goto_label=Label("unassigned")):
        if self.expr.operator.value in ["==", "!=", "<", ">", "<=", ">="]:
            frame.open_frame()
            self.expr.left.generate_opcodes(frame.current_frame)
            left_storage = frame.close_frame().return_storage
            frame.open_frame()
            self.expr.right.generate_opcodes(frame.current_frame)
            right_storage = frame.close_frame().return_storage
            operator = {
                "==": OpcodeKind.bne,
                "!=": OpcodeKind.beq,
                "<=": OpcodeKind.bgt,
                ">=": OpcodeKind.blt,
                "<": OpcodeKind.bge,
                ">": OpcodeKind.ble,
            }[self.expr.operator.value]
            frame.push_opcode(Instruction(
                operator,
                [left_storage, right_storage, goto_label]
            ))

        else:
            frame.open_frame()
            self.expr.generate_opcodes(frame.current_frame)
            condition_storage = frame.close_frame().return_storage
            frame.push_opcode(Instruction(
                OpcodeKind.beq,
                [condition_storage, Const(0), goto_label]
            ))


class IfStatement(Terminal):
    def __init__(self, condition: 'Condition', body: 'Body', else_st: Union['Body', 'IfStatement'] = None):
        self.condition = condition
        self.body = body
        self.else_statement = else_st

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : ST_IF LPAREN condition RPAREN LBRACE body RBRACE")
        def if_def(p: tuple[Token, Token, 'Condition', Token, Token, 'Body', Token]):
            return IfStatement(p[2], p[5])

        @gen.production(
            f"{this.name} : ST_IF LPAREN condition RPAREN "
            f"LBRACE body RBRACE ELSE "
            f"LBRACE body RBRACE")
        def if_else_def(p: tuple[Token, Token, 'Condition', Token, Token, 'Body', Token, Token, Token, 'Body', Token]):
            return IfStatement(p[2], p[5], p[9])

        @gen.production(
            f"{this.name} : ST_IF LPAREN condition RPAREN "
            f"LBRACE body RBRACE "
            f"ELSE if_statement")
        def if_else_if_def(p: tuple[Token, Token, 'Condition', Token, Token, 'Body', Token, Token, 'IfStatement']):
            return IfStatement(p[2], p[5], p[8])

    def evaluate(self, frame: 'ExecutionFrame'):
        if self.condition.evaluate(frame):
            self.body.evaluate(frame)
        elif self.else_statement:
            self.else_statement.evaluate(frame)

    def generate_opcodes(self, frame: 'CodeGenFrame', if_end_label_: Label = None):
        if self.else_statement:
            if_else_label = Label(f"if_{frame.data.label_counter['if']}_else")
            if_end_label = if_end_label_ or Label(f"if_{frame.data.label_counter['if']}_end")

        else:
            if_else_label = Label(f"if_{frame.data.label_counter['if']}")
            if_end_label = if_end_label_

        frame.data.label_counter['if'] += 1

        self.condition.generate_opcodes(frame.open_frame(), goto_label=if_else_label)
        frame.close_frame()

        self.body.generate_opcodes(frame.open_frame())
        frame.close_frame()

        if if_end_label:
            frame.push_opcode(Instruction(
                OpcodeKind.jmp,
                [if_end_label]
            ))

        frame.push_opcode(if_else_label)

        if self.else_statement:
            if isinstance(self.else_statement, Body):
                self.else_statement.generate_opcodes(frame.open_frame())
                frame.close_frame()

            elif isinstance(self.else_statement, IfStatement):
                self.else_statement.generate_opcodes(frame.open_frame(), if_end_label_=if_end_label)
                frame.close_frame()

            else:
                raise AssertionError(
                    f"Field else_statement of {self.__class__} must be {Body} or {IfStatement}, "
                    f"got {type(self.else_statement)}.")

            if not if_end_label_:
                frame.push_opcode(if_end_label)


class ForStatement(Terminal):
    def __init__(self, startup: 'Assign', condition: 'Expression', increment: 'Expression', body: 'Body'):
        self.startup = startup
        self.condition = condition
        self.increment = increment
        self.body = body

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : ST_FOR LPAREN "
                        f"assign SEMI_COLON expression SEMI_COLON expression "
                        f"RPAREN LBRACE body RBRACE")
        def example_def(p: tuple[
            Token, Token,
            'Assign', Token, 'Expression', Token, 'Expression',
            Token, Token, 'Body', Token
        ]):
            return ForStatement(p[2], p[4], p[6], p[9])

    def evaluate(self, frame: 'ExecutionFrame'):
        self.startup.evaluate(frame)
        while self.condition.evaluate(frame):
            self.body.evaluate(frame)
            self.increment.evaluate(frame)

    def generate_opcodes(self, frame: 'CodeGenFrame'):
        frame.open_frame()
        self.startup.generate_opcodes(frame.current_frame)
        frame.close_frame()

        loop_label = Label(f"loop_for_{frame.data.label_counter['loop_for']}")
        end_label = Label(loop_label.name + "_end")

        frame.push_opcode(loop_label)
        frame.data.label_counter['loop_for'] += 1

        frame.open_frame()
        Condition(self.condition).generate_opcodes(frame.current_frame, end_label)
        frame.close_frame()

        frame.open_frame()
        self.body.generate_opcodes(frame.current_frame)
        frame.close_frame()
        frame.open_frame()
        self.increment.generate_opcodes(frame.current_frame)
        frame.close_frame()

        frame.push_opcode(Instruction(
            OpcodeKind.jmp,
            [loop_label]
        ))
        frame.push_opcode(end_label)
