from analyzers import Parser, Lexer
from ast_evaluator import AstEvaluator
from code_generation.code_generator import CodeGenerator
from stopwatch import Stopwatch
from terminal import Terminal, Program
from utils import TerminalUtil


def main():
    lexer = Lexer()
    parser = Parser()

    with open("example.fcpu") as f:
        code = f.read()

    watch = Stopwatch("Lexing code to tokens").start()
    tokens = lexer.lex(code)
    watch.stop()

    print("Tokens: ")
    [print("  ", token) for token in tokens]
    print()
    tokens.idx = 0

    watch = Stopwatch("Parsing tokens to AST").start()
    term: Program = parser.parse(tokens)
    watch.stop()

    print("AST:")
    print(TerminalUtil.get_pretty(term))
    print()

    print("Evaluating")
    evaluator = AstEvaluator()
    result = evaluator.evaluate(term)
    print("   result: ", result)
    print()

    watch = Stopwatch("Generating opcodes from AST").start()
    opcodes = CodeGenerator.generate_code(term)
    watch.stop()
    print("Opcodes:")
    [print("  ", opcode) for opcode in opcodes]


if __name__ == '__main__':
    main()
