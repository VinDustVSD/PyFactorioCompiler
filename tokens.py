from enum import Enum


class TokenKind(Enum):
    NUMBER_SCI_FORM = [r"\d+e([\+\-]?\d+)"]
    NUMBER_FLOAT = [r"\d+\.\d+"]
    NUMBER_INT = [r"\d+"]

    # Factorio(and f-cpu) special tokens
    SIGNAL = [
        r"\[virtual\-signal=signal-[\w\-]+\]",
        r"\[item=[\w\-]+\]",
        r"\[entity=[\w\-]+\]"
    ]
    WIRE_TYPE = [r"red", r"green"]

    # Keywords
    FUNC_DEF = [r"func"]
    ST_IF = [r"if"]
    ELSE = [r"else"]
    ST_FOR = [r"for"]
    ST_WHILE = [r"while"]
    RETURN = [r"return"]
    YIELD = [r"yield"]
    BREAK = [r"BREAK"]

    # Punctuation
    COMMA = [","]
    COLON = [":"]
    SEMI_COLON = [";"]

    # Brackets
    LPAREN = [r"\("]
    RPAREN = [r"\)"]
    LBRACE = [r"\{"]
    RBRACE = [r"\}"]

    # Unary operators
    INCREMENT = [r"\+\+"]
    DECREMENT = [r"\-\-"]

    # Comparison operators
    OP_CMP_EQ = [r"=="]
    OP_CMP_NE = [r"!="]
    OP_CMP_GE = [r">="]
    OP_CMP_LE = [r"<="]
    OP_CMP_GT = [r">"]
    OP_CMP_LT = [r"<"]

    # Assign operators
    ASSIGN_SUM = [r"\+="]
    ASSIGN_SUB = [r"\-="]
    ASSIGN_MUL = [r"\*="]
    ASSIGN_DIV = [r"/="]
    ASSIGN_POW = [r"\*\*="]
    ASSIGN = ["="]

    # Binary Operators
    OP_POW = [r"\*\*"]
    OP_SUM = [r"\+"]
    OP_SUB = [r"\-"]
    OP_MUL = [r"\*"]
    OP_DIV = [r"\/"]
    OP_MOD = [r"\%"]

    # Other
    IDENTIFIER = [r"\w+"]
