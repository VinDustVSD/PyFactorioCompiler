from enum import Enum


class CompilerSettings:
    def __init__(self, target: 'CompilationTarget'):
        self.compilation_target = target


class CompilationTarget(Enum):
    raw_fcpu = 1
    raw_combinators = 2
    fcpu_batch = 4 + 1
    combinator_batch = 8 + 2
