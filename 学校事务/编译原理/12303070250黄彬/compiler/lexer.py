from typing import List, Tuple

from .models import Diagnostic, Token


KEYWORDS = {
    "const": 100,
    "int": 101,
    "float": 102,
    "char": 103,
    "void": 104,
    "return": 105,
    "if": 106,
    "else": 107,
    "while": 108,
    "do": 109,
    "for": 110,
    "break": 111,
    "continue": 112,
}

OPERATORS = {
    "==": 201,
    "!=": 202,
    "<=": 203,
    ">=": 204,
    "&&": 205,
    "||": 206,
    "=": 207,
    ">": 208,
    "<": 209,
    "+": 210,
    "-": 211,
    "*": 212,
    "/": 213,
    "!": 214,
    "%": 215,
}

SEPARATORS = {
    ";": 301,
    ",": 302,
    "(": 303,
    ")": 304,
    "{": 305,
    "}": 306,
    "[": 307,
    "]": 308,
}

IDENTIFIER_CODE = 700
INT_LITERAL_CODE = 401
FLOAT_LITERAL_CODE = 402
CHAR_LITERAL_CODE = 403
STRING_LITERAL_CODE = 404
SUPPORTED_CHAR_ESCAPES = {"n", "t", "r", "0", "'", "\\"}
SUPPORTED_STRING_ESCAPES = {"n", "t", "r", "0", '"', "\\"}


class Lexer:
    def tokenize(self, source: str) -> Tuple[List[Token], List[Diagnostic]]:
        tokens: List[Token] = []
        diagnostics: List[Diagnostic] = []
        i = 0
        line = 1
        column = 1

        while i < len(source):
            ch = source[i]

            if ch in " \t\r":
                i += 1
                column += 1
                continue

            if ch == "\n":
                i += 1
                line += 1
                column = 1
                continue

            if source.startswith("//", i):
                while i < len(source) and source[i] != "\n":
                    i += 1
                    column += 1
                continue

            if source.startswith("/*", i):
                start_line = line
                start_column = column
                i += 2
                column += 2
                closed = False
                while i < len(source):
                    if source.startswith("*/", i):
                        i += 2
                        column += 2
                        closed = True
                        break
                    if source[i] == "\n":
                        i += 1
                        line += 1
                        column = 1
                    else:
                        i += 1
                        column += 1
                if not closed:
                    diagnostics.append(Diagnostic("lexer", start_line, "L001", f"unclosed comment at column {start_column}"))
                continue

            if ch.isalpha() or ch == "_":
                start = i
                start_column = column
                while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                    i += 1
                    column += 1
                text = source[start:i]
                if text in KEYWORDS:
                    tokens.append(Token(text, KEYWORDS[text], line, start_column, "keyword"))
                else:
                    tokens.append(Token(text, IDENTIFIER_CODE, line, start_column, "identifier"))
                continue

            if ch.isdigit():
                start = i
                start_column = column
                has_dot = False
                while i < len(source) and (source[i].isdigit() or source[i] == "."):
                    if source[i] == ".":
                        if has_dot:
                            break
                        has_dot = True
                    i += 1
                    column += 1
                text = source[start:i]
                code = FLOAT_LITERAL_CODE if has_dot else INT_LITERAL_CODE
                kind = "float_literal" if has_dot else "int_literal"
                tokens.append(Token(text, code, line, start_column, kind))
                continue

            if ch == "'":
                start = i
                start_column = column
                i += 1
                column += 1
                while i < len(source):
                    if source[i] == "\n" or source[i] == "'":
                        break
                    if source[i] == "\\":
                        i += 1
                        column += 1
                        if i >= len(source) or source[i] == "\n":
                            break
                    i += 1
                    column += 1
                if i < len(source) and source[i] == "'":
                    i += 1
                    column += 1
                    text = source[start:i]
                    payload = text[1:-1]
                    is_ordinary_char = len(payload) == 1 and payload != "\\"
                    is_escape_char = len(payload) == 2 and payload[0] == "\\" and payload[1] in SUPPORTED_CHAR_ESCAPES
                    if is_ordinary_char or is_escape_char or payload:
                        tokens.append(Token(text, CHAR_LITERAL_CODE, line, start_column, "char_literal"))
                    else:
                        diagnostics.append(Diagnostic("lexer", line, "L004", f"malformed char literal at column {start_column}"))
                else:
                    diagnostics.append(Diagnostic("lexer", line, "L002", f"unclosed char literal at column {start_column}"))
                continue

            if ch == '"':
                start = i
                start_column = column
                i += 1
                column += 1
                closed = False
                valid = True
                while i < len(source):
                    if source[i] == "\n":
                        break
                    if source[i] == '"':
                        closed = True
                        i += 1
                        column += 1
                        break
                    if source[i] == "\\":
                        i += 1
                        column += 1
                        if i >= len(source) or source[i] not in SUPPORTED_STRING_ESCAPES:
                            valid = False
                            break
                    i += 1
                    column += 1
                if closed and valid:
                    tokens.append(Token(source[start:i], STRING_LITERAL_CODE, line, start_column, "string_literal"))
                else:
                    diagnostics.append(Diagnostic("lexer", line, "L005", f"malformed string literal at column {start_column}"))
                continue

            two = source[i : i + 2]
            if two in OPERATORS:
                tokens.append(Token(two, OPERATORS[two], line, column, "operator"))
                i += 2
                column += 2
                continue

            if ch in OPERATORS:
                tokens.append(Token(ch, OPERATORS[ch], line, column, "operator"))
                i += 1
                column += 1
                continue

            if ch in SEPARATORS:
                tokens.append(Token(ch, SEPARATORS[ch], line, column, "separator"))
                i += 1
                column += 1
                continue

            diagnostics.append(Diagnostic("lexer", line, "L003", f"unknown character {ch!r} at column {column}"))
            i += 1
            column += 1

        return tokens, diagnostics
