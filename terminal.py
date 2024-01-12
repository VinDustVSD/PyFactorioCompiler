from typing import Type, Optional, TYPE_CHECKING, Union

from rply import ParserGenerator, Token

from code_generation.code_generator import CodeGenFrame
from code_generation.opcodes import Instruction, OpcodeKind, Label
from code_generation.stacks import Register, MemoryCell, Const
from tokens import TokenKind

if TYPE_CHECKING:
    from ast_evaluator import ExecutionFrame


class Terminal:
    name = None

    @staticmethod
    def gen_productions(this_class: Type['Terminal'], gen: ParserGenerator):
        pass

    def evaluate(self, frame: 'ExecutionFrame'):
        raise NotImplementedError(f"Evaluating not implemented in {self.__class__}.")

    def generate_opcodes(self, frame: CodeGenFrame):
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

    def generate_opcodes(self, frame: CodeGenFrame):
        super().generate_opcodes(frame)


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

    def generate_opcodes(self, frame: CodeGenFrame):
        super().generate_opcodes(frame)


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
        for arg in self.args.items:
            frame.set_local(arg.arg_name.value, 0)
        return self.body.evaluate(frame)

    def generate_opcodes(self, frame: CodeGenFrame):
        args = {arg.arg_name.value: arg for arg in self.args.items}

        def on_get_storage(variable):
            if not variable.n_storage_:
                var_frame = frame.open_frame()
                reg = frame.reg_stack.pop()
                sig = None
                for sig_ in frame.sig_stack.available:
                    if args[variable.a_name].signal == str(sig_):
                        sig = frame.sig_stack.pop(sig_.idx)
                        break

                if not sig:
                    sig = frame.sig_stack.pop()

                var_frame.push_opcode(Instruction(
                    OpcodeKind.fig if args[variable.a_name].wire == "green" else OpcodeKind.fir,
                    [reg, sig]
                ))
                variable.n_storage_ = reg
                frame.close_frame()

            return variable.n_storage_

        for arg in self.args.items:
            var = Variable(arg.arg_name.value, None)
            var.n_on_get_storage = on_get_storage
            frame.set_local(arg.arg_name.value, var)

        frame.open_frame()
        self.body.generate_opcodes(frame.current_frame)
        frame.close_frame()


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
            if item.name in [Yield.name, Return.name]:
                return output

    def generate_opcodes(self, frame: CodeGenFrame):
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

    def generate_opcodes(self, frame: CodeGenFrame):
        super().generate_opcodes(frame)


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
        frame.open_frame()
        self.value.generate_opcodes(frame.current_frame)
        value_frame = frame.close_frame()
        reg = value_frame.return_storage

        if isinstance(reg, Const):
            reg = frame.reg_stack.pop()
            frame.push_opcode(Instruction(
                OpcodeKind.mov,
                [reg, value_frame.return_storage]
            ))

        # SemanticAnalyzer must check if assign expression returns value, right?
        var = Variable(self.a_name, reg)
        frame.set_local(self.a_name, var)


class Condition(Terminal):
    def __init__(self, expr: 'Expression'):
        self.expr = expr

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : {Expression.name}")
        def example_def(p: tuple[Expression]):
            return Condition(p[0])

    def evaluate(self, frame: 'ExecutionFrame'):
        return self.expr.evaluate(frame)

    def generate_opcodes(self, frame: CodeGenFrame, goto_label=Label("unassigned")):
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
    def __init__(self, condition: Condition, body: Body, else_st: Union[Body, 'IfStatement'] = None):
        self.condition = condition
        self.body = body
        self.else_statement = else_st

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : ST_IF LPAREN {Condition.name} RPAREN LBRACE {Body.name} RBRACE")
        def if_def(p: tuple[Token, Token, Condition, Token, Token, Body, Token]):
            return IfStatement(p[2], p[5])

        @gen.production(
            f"{this.name} : ST_IF LPAREN {Condition.name} RPAREN "
            f"LBRACE {Body.name} RBRACE ELSE "
            f"LBRACE {Body.name} RBRACE")
        def if_else_def(p: tuple[Token, Token, Condition, Token, Token, Body, Token, Token, Token, Body, Token]):
            return IfStatement(p[2], p[5], p[9])

        @gen.production(
            f"{this.name} : ST_IF LPAREN {Condition.name} RPAREN "
            f"LBRACE {Body.name} RBRACE "
            f"ELSE {IfStatement.name}")
        def if_else_if_def(p: tuple[Token, Token, Condition, Token, Token, Body, Token, Token, IfStatement]):
            return IfStatement(p[2], p[5], p[8])

    def evaluate(self, frame: 'ExecutionFrame'):
        if self.condition.evaluate(frame):
            self.body.evaluate(frame)
        elif self.else_statement:
            self.else_statement.evaluate(frame)

    def generate_opcodes(self, frame: CodeGenFrame, if_end_label_: Label = None):
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
    def __init__(self, startup: Assign, condition: 'Expression', increment: 'Expression', body: 'Body'):
        self.startup = startup
        self.condition = condition
        self.increment = increment
        self.body = body

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : ST_FOR LPAREN "
                        f"{Assign.name} SEMI_COLON {Expression.name} SEMI_COLON {Expression.name} "
                        f"RPAREN LBRACE {Body.name} RBRACE")
        def example_def(p: tuple[
            Token, Token,
            Assign, Token, Expression, Token, Expression,
            Token, Token, Body, Token
        ]):
            return ForStatement(p[2], p[4], p[6], p[9])

    def evaluate(self, frame: 'ExecutionFrame'):
        self.startup.evaluate(frame)
        while self.condition.evaluate(frame):
            self.body.evaluate(frame)
            self.increment.evaluate(frame)

    def generate_opcodes(self, frame: CodeGenFrame):
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
            [frame.data.locals[self.identifier].n_storage]
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
            self.left = frame.data.locals[self.left.a_name]

        if isinstance(self.right, Variable) and self.right.a_name in frame.data.locals:
            self.right = frame.data.locals[self.right.a_name]

        frame.open_frame()
        self.left.generate_opcodes(frame.current_frame)
        left_reg_or_val = frame.close_frame().return_storage

        frame.open_frame()
        self.right.generate_opcodes(frame.current_frame)
        right_reg_or_val = frame.close_frame().return_storage

        if isinstance(left_reg_or_val, Register) or isinstance(left_reg_or_val, MemoryCell):
            output_register = left_reg_or_val

        elif isinstance(right_reg_or_val, Register) or isinstance(right_reg_or_val, MemoryCell):
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

    def generate_opcodes(self, frame: CodeGenFrame):
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

    def generate_opcodes(self, frame: CodeGenFrame):
        if self.a_name in frame.data.locals:
            self.n_storage_ = frame.data.locals[self.a_name].n_storage

        frame.return_storage = self.n_storage_


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
