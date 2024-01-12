# print("Hello world")
# import sys
#
# print(f"Package: {__package__}\nVersion: {ascii(sys.version)}\nVerInfo: {sys.version_info}\nSysPath:")
# [print(f"\t{path}") for path in sys.path]

from analyzers import Parser, Lexer
from ast_evaluator import AstEvaluator
from code_generation.code_generator import CodeGenerator
from stopwatch import Stopwatch
from terminal import Program
from utils import TerminalUtil


def compile_file(path: str):
    lexer = Lexer()
    parser = Parser()

    with open(path) as f:
        code = f.read()

    watch = Stopwatch("Lexing code to tokens").start()
    tokens = lexer.lex(code)
    watch.stop()

    watch = Stopwatch("Parsing tokens to AST").start()
    term: Program = parser.parse(tokens)
    watch.stop()

    # print("AST:")
    # print(TerminalUtil.get_pretty(term))
    # print()
    import sys
    print("SysArgs", sys.argv)

    print("Evaluating")
    evaluator = AstEvaluator()
    result = evaluator.evaluate(term)
    print("   result: ", result)
    print()

    watch = Stopwatch("Generating opcodes from AST").start()
    opcodes = CodeGenerator.generate_code(term)
    watch.stop()
    print("Opcodes:")
    [print(opcode.to_string()) for opcode in opcodes]
    # TODO: Implement comparison in expressions


def main():
    compile_file("ex1.fcpu")


if __name__ == '__main__':
    main()
