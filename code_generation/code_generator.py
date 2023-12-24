from code_generation.opcodes import OpcodeKind, Instruction
from code_generation.stacks import RegisterStack, TypeSignal, SignalStack, TypeSignalKind
from terminal import Program, Assign


class CodeGenerator:
    def __init__(self):
        pass

    @staticmethod
    def generate_code(ast: Program, entry_point_name="Main"):
        reg_stack = RegisterStack()
        sig_stack = SignalStack({TypeSignalKind.virtual: TypeSignalKind.virtual.value})
        opcodes = []

        # TODO: Take it to Terminals
        for arg in ast.entry_point.args.items:
            reg = reg_stack.pop()
            opcodes.append(Instruction(
                OpcodeKind.fig if arg.wire == "green" else OpcodeKind.fir,
                [reg, sig_stack.pop()]
            ))

        for statement in ast.entry_point.body.items:
            if statement.name == Assign.name:
                ...
            elif ...:
                ...

        return opcodes
