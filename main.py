from analyzers import Parser, Lexer
from ast_evaluator import AstEvaluator
from code_generation.code_generator import CodeGenerator
from stopwatch import Stopwatch
from terminal.program import Program
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

    watch = Stopwatch("Generating opcodes from AST").start()
    opcodes = CodeGenerator.generate_code(term)
    watch.stop()
    print("Opcodes:")
    [print(opcode.to_string()) for opcode in opcodes]

    print()
    watch = Stopwatch("Evaluating").start()
    evaluator = AstEvaluator()
    result = evaluator.evaluate(term)
    print(f"result({result}) ", end="")
    watch.stop()
    # TODO: Implement comparison in expressions


def main():
    compile_file("ex1.fcpu")


if __name__ == '__main__':
    main()
