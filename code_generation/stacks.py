from enum import Enum
from string import ascii_uppercase, digits


class SignalStack:
    def __init__(self, signals: dict['TypeSignalKind', list[str]]):
        self._signals = tuple(
            TypeSignal(i, self, kind, sig_name) for i, kind in enumerate(signals) for sig_name in signals[kind]
        )
        self._available = list(self._signals)

    @property
    def available(self):
        return list(self._available)

    @property
    def reserved(self):
        return list(filter(lambda a: a.reserved, self._signals))

    def pop(self, index: int = 0) -> 'TypeSignal':
        return self._available.pop(index)

    def dispose(self, sig: 'TypeSignal'):
        if not isinstance(sig, TypeSignal):
            raise TypeError(f"Arg1 must be sig class, got {type(sig)}")

        if sig not in self._signals:
            raise ValueError("Can't dispose sig to not it's own stack.")

        self._available.append(sig)


class TypeSignalKind(Enum):
    virtual = ascii_uppercase + digits


class TypeSignal:
    def __init__(self, index: int, stack: SignalStack, sig_type: TypeSignalKind, sig_name: str):
        self._idx = index
        self._stack = stack
        self.sig_type = sig_type
        self.sig_name = sig_name

    def __repr__(self):
        return f"[{self.sig_type.name}-{self.sig_name}]"

    @property
    def idx(self):
        return self._idx

    @property
    def reserved(self):
        return self not in self._stack.available

    def dispose(self):
        self._stack.dispose(self)


class Signal:
    def __init__(self):
        pass


class MemoryChannel:
    def __init__(self):
        pass


class InputSelector:
    def __init__(self):
        pass


class OutputSelector:
    def __init__(self):
        pass


class RegisterStack:
    def __init__(self, size=8):
        self._registers = tuple(Register(i, self) for i in range(size))
        self._available = list(self._registers)

    @property
    def available(self):
        return list(self._available)

    @property
    def reserved(self):
        return list(filter(lambda a: a.reserved, self._registers))

    def pop(self, index: int = 0) -> 'Register':
        return self._available.pop(index)

    def dispose(self, register: 'Register'):
        if not isinstance(register, Register):
            raise TypeError(f"Arg1 must be sig class, got {type(register)}")

        if register not in self._registers:
            raise ValueError("Can't dispose sig to not it's own stack.")

        self._available.append(register)


class Register:
    def __init__(self, index: int, stack: RegisterStack):
        self._idx = index
        self._stack = stack

    def __repr__(self):
        return f"r{self._idx + 1}"

    @property
    def idx(self):
        return self._idx

    @property
    def reserved(self):
        return self not in self._stack.available

    def dispose(self):
        self._stack.dispose(self)
