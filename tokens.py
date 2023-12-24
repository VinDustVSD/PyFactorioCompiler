from enum import Enum


class TokenKind(Enum):
    NUMBER = [r"\d+(\.\d+)?"]

    # Factorio(and f-cpu) special tokens
    # SIGNAL = [
    #     r"\[virtual\-signal=[\w\-]+\]",
    #     r"\[item=[\w\-]+\]",
    #     r"\[entity=[\w\-]+\]"
    # ]
    WIRE_TYPE = [r"red", r"green"]

    # Keywords
    FUNC_DEF = [r"func"]
    RETURN = [r"return"]

    # Punctuation
    COMMA = [","]
    COLON = [":"]
    SEMI_COLON = [";"]

    # Brackets
    LPAREN = [r"\("]
    RPAREN = [r"\)"]
    LBRACE = [r"\{"]
    RBRACE = [r"\}"]

    # Binary Operators
    OP_POW = [r"\*\*"]
    OP_SUM = [r"\+"]
    OP_SUB = [r"\-"]
    OP_MUL = [r"\*"]
    OP_DIV = [r"\/"]

    # Comparison operators
    # OP_CMP_EQ = ["OP_CMP_EQ"]
    # OP_CMP_NE = ["OP_CMP_NE"]

    # Assign operators
    ASSIGN = ["="]

    # Other
    IDENTIFIER = [r"\w+"]
