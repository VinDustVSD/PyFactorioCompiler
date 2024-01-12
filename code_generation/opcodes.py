import re
from enum import Enum
from typing import Union

from code_generation.stacks import Register, TypeSignal, Signal, MemoryCell, InputSelector, OutputCell, Const


class OpcodeKindRule:
    def __init__(self, string: str):
        split = list(map(str.strip, string.split("#")))
        self.comment = "\n".join(split[1:])
        self.args = [OpcodeKindRuleArg(arg) for arg in split[0].split()]

    def assert_unfit_args(self, args: list):
        have_multi_args = any(arg.multiple for arg in self.args)
        if len(args) < len(self.args):
            raise ValueError(
                f"Expected {len(self.args)}{' or more' if have_multi_args else ''} {self.args}, "
                f"got {len(args)} {tuple(arg.__class__.__name__ + '(' + str(arg) + ')' for arg in args)} args.")

        if len(args) > len(self.args) and not have_multi_args:
            raise ValueError(f"Expected {len(self.args)}, got {len(args)} args.")

        for i in range(len(args)-1, -1, -1):
            ex_idx = i - (len(args) - len(self.args))
            ex_arg = self.args[max(0, ex_idx)]
            arg = args[i]

            if type(arg) not in [type_.value for type_ in ex_arg.types]:
                raise ValueError(f"Wrong instruction argument '{arg.__class__.__name__}', "
                                 f"expected {ex_arg.name}{[arg.name for arg in ex_arg.types]}.")

        return True


class Instruction:
    def __init__(self, kind: 'OpcodeKind', args: list[Union['Register', 'Const', 'Label']]):
        self.kind = kind
        self.args = args
        if isinstance(self.kind.value, OpcodeKindRule):
            self.kind.value.assert_unfit_args(args)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.kind.name} {' '.join(map(str, self.args))})"

    def to_string(self):
        return f"{self.kind.name} {' '.join(map(str, self.args))}"


class Label(Instruction):
    def __init__(self, name: str):
        self.name = name
        super().__init__(OpcodeKind.n_label, [])

    def __repr__(self):
        return f"{self.__class__.__name__}(:{self.name})"

    def __str__(self):
        return ":" + self.name

    def to_string(self):
        return str(self)


class OpcodeArgType(Enum):
    C = Const
    T = TypeSignal
    CT = Signal
    R = Register
    M = MemoryCell
    I = InputSelector
    O = OutputCell

    A = int
    L = Label
    S = None


class OpcodeKindRuleArg:
    def __init__(self, string: str):
        match = re.fullmatch(r"(\w+)(\.\.\.)?\[([CTRMIOALS/]+)]", string)
        if not match:
            raise ValueError(f"Wrong opcode arg rule '{string}'.")

        groups = match.groups()
        types = groups[2].split("/")
        _types = []
        args_types = [key for key in OpcodeArgType.__members__]
        for arg_type in types:
            if not arg_type or arg_type not in args_types:
                raise ValueError(f"Wrong opcode arg rule '{string}' -> invalid arg type '{arg_type}', "
                                 f"must be one of {args_types}.")
            _types.append(OpcodeArgType[arg_type])

        self.name = groups[0]
        self.multiple = bool(groups[1])
        self.types = tuple(_types)

    def __repr__(self):
        return f"Arg({self.name}{'...' if self.multiple else ''}{[type_.name for type_ in self.types]})"


class OpcodeKind(Enum):
    jmp = OpcodeKindRule("addr[C/A/L/R] # Jump to addr or label")
    dec = OpcodeKindRule("dst[R] # dst = dst + 1")
    inc = OpcodeKindRule("dst[R] # dst = dst - 1")
    ble = OpcodeKindRule("a[C/S/R] b[C/S/R] addr[C/A/L/R] # if a <= b then jmp addr offset")
    bge = OpcodeKindRule("a[C/S/R] b[C/S/R] addr[C/A/L/R] # if a >= b then jmp addr offset")
    blt = OpcodeKindRule("a[C/S/R] b[C/S/R] addr[C/A/L/R] # if a < b then jmp addr offset")
    bgt = OpcodeKindRule("a[C/S/R] b[C/S/R] addr[C/A/L/R] # if a > b then jmp addr offset")
    beq = OpcodeKindRule("a[C/S/R] b[C/S/R] addr[C/A/L/R] # if a == b then jmp addr offset")
    bne = OpcodeKindRule("a[C/S/R] b[C/S/R] addr[C/A/L/R] # if a != b then jmp addr offset")
    tle = OpcodeKindRule("a[C/S/R] b[C/S/R] # a <= b")
    tge = OpcodeKindRule("a[C/S/R] b[C/S/R] # a >= b")
    tlt = OpcodeKindRule("a[C/S/R] b[C/S/R] # a < b")
    tgt = OpcodeKindRule("a[C/S/R] b[C/S/R] # a < b")
    teq = OpcodeKindRule("a[C/S/R] b[C/S/R] # a == b")
    tne = OpcodeKindRule("a[C/S/R] b[C/S/R] # a != b")
    add = OpcodeKindRule("dst[R] src[C/R] val[C/R] # _dst_ = _src_ + _val_")
    sub = OpcodeKindRule("dst[R] src[C/R] val[C/R] # _dst_ = _src_ - _val_")
    mul = OpcodeKindRule("dst[R] src[C/R] val[C/R] # _dst_ = _src_ * _val_")
    div = OpcodeKindRule("dst[R] src[C/R] val[C/R] # _dst_ = _src_ / _val_")
    pow = OpcodeKindRule("dst[R] src[C/R] val[C/R] # _dst_ = _src_ ^ _val_")
    n_comment = OpcodeKindRule("")
    n_label = OpcodeKindRule("")
    nop = OpcodeKindRule("# No operation")
    clr = OpcodeKindRule("# Clear")
    mov = OpcodeKindRule("dst...[R/O] val[C/T/CT/R] # Copy signal from source to destination")
    fir = OpcodeKindRule("dst[R/O] type[T/R] # Find _type_ in red_input, then assign to _dst_")
    fig = OpcodeKindRule("dst[R/O] type[T/R] # Find _type_ in green_input, then assign to _dst_")
