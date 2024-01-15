from typing import Type, TYPE_CHECKING

from rply import Token, ParserGenerator
from terminal.base import Terminal, Variable
from code_generation.opcodes import Instruction, OpcodeKind

if TYPE_CHECKING:
    from ast_evaluator import ExecutionFrame
    from code_generation.code_generator import CodeGenFrame
    from terminal.bodies import Body
    from terminal.arguments import DefArgs


class Function(Terminal):
    def __init__(self, name: Token, args: 'DefArgs', body: 'Body'):
        self.a_name: str = name.value
        self.args = args
        self.body = body
        self.n_is_entry_point = False

    @staticmethod
    def gen_productions(this: Type[Terminal], gen: ParserGenerator):
        @gen.production(f"{this.name} : FUNC_DEF IDENTIFIER LPAREN def_args RPAREN LBRACE body RBRACE")
        def example_def(p: tuple[Token, Token, Token, 'DefArgs', Token, Token, 'Body', Token]):
            return Function(p[1], p[3], p[6])

    def evaluate(self, frame: 'ExecutionFrame'):
        frame.new_frame()
        for arg in self.args.items:
            frame.set_local(arg.arg_name.value, 0)
        return self.body.evaluate(frame)

    def generate_opcodes(self, frame: 'CodeGenFrame'):
        if self.n_is_entry_point:
            frame.push_opcode(Instruction(OpcodeKind.clr, []))

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
            var.n_on_get_storage(var)
            frame.set_local(arg.arg_name.value, var)

        self.body.generate_opcodes(frame.open_frame())
        frame.close_frame()
