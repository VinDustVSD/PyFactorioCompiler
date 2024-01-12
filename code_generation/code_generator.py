from typing import TYPE_CHECKING

from code_generation.opcodes import Instruction
from code_generation.stacks import RegisterStack, SignalStack, TypeSignalKind, OutputStack, Register
from settings import CompilerSettings, CompilationTarget

if TYPE_CHECKING:
    from terminal import Program, Variable


class CodeGenFrame:
    def __init__(self, cg_data: 'CodeGenData'):
        self.data = cg_data
        self.return_storage = None

    def push_opcode(self, opcode: Instruction):
        self.data.opcodes.append(opcode)

    @property
    def reg_stack(self):
        return self.data.reg_stack

    def try_pop_reg(self, index: int):
        if len(self.reg_stack.available) == 0:
            reg_vars = filter(lambda a: isinstance(a.n_storage_, Register), self.data.locals.values())
            var: Variable = list(reg_vars)[0]

        return self.reg_stack.pop(index)

    @property
    def sig_stack(self):
        return self.data.sig_stack

    @property
    def last_archive_frame(self):
        return self.last_archive_frame

    @property
    def current_frame(self):
        return self.data.current_frame

    def open_frame(self):
        return self.data.open_frame()

    def close_frame(self):
        return self.data.close_frame()

    def set_local(self, key, value):
        self.data.set_local(key, value)

    def get(self, name):
        return self.data.get_local_or_global(name)


class CodeGenData:
    def __init__(self):
        self.reg_stack = RegisterStack()
        self.sig_stack = SignalStack({
            TypeSignalKind.virtual_signal: TypeSignalKind.virtual_signal.value,
            TypeSignalKind.item: TypeSignalKind.item.value
        })
        self.out_stack = OutputStack()
        self.opcodes = []
        self.globals = {}
        self.locals = {}
        self.settings: CompilerSettings = CompilerSettings(CompilationTarget.raw_fcpu)
        self._frame_archive: list[CodeGenFrame] = []
        self._frame_stack: list[CodeGenFrame] = [CodeGenFrame(self)]
        self.label_counter: dict[str, int] = {
            "loop_for": 0,
            "if": 0
        }

    @property
    def last_archive_frame(self):
        return self._frame_archive[-1] if len(self._frame_archive) > 0 else None

    @property
    def registers_in_locals(self):
        return [i.n_storage_ for i in self.locals.values()]

    @property
    def current_frame(self):
        return self._frame_stack[-1]

    def open_frame(self):
        self._frame_stack.append(CodeGenFrame(self))
        return self._frame_stack[-1]

    def close_frame(self):
        if len(self._frame_stack) <= 1:
            raise IndexError("First(global) frame cannot be closed.")

        self._frame_archive.append(self._frame_stack.pop())
        return self.last_archive_frame

    def set_local(self, key, value):
        self.locals[key] = value

    def get_local_or_global(self, name):
        return self.locals.get(name) or self.globals.get(name)


class CodeGenerator:
    @staticmethod
    def generate_code(ast: 'Program', entry_point_name="Main"):
        env = CodeGenData()
        ast.entry_point.generate_opcodes(env.current_frame)
        return env.opcodes
