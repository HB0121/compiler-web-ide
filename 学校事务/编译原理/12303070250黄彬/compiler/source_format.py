INDENT = "    "


def format_source(source: str) -> str:
    logical_lines = _split_logical_lines(source)
    formatted = []
    indent_level = 0

    for raw_line in logical_lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("}"):
            indent_level = max(0, indent_level - 1)
        formatted.append(f"{INDENT * indent_level}{line}")
        if line.endswith("{"):
            indent_level += 1

    return "\n".join(formatted) + ("\n" if formatted else "")


def _split_logical_lines(source: str) -> list[str]:
    lines: list[str] = []
    current: list[str] = []
    i = 0
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False
    escape = False

    def emit() -> None:
        text = "".join(current).strip()
        if text:
            lines.append(_normalize_brace_spacing(text))
        current.clear()

    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""

        if in_line_comment:
            current.append(ch)
            if ch == "\n":
                emit()
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            current.append(ch)
            if ch == "*" and nxt == "/":
                current.append(nxt)
                i += 2
                in_block_comment = False
                continue
            i += 1
            continue

        if not in_string and not in_char and ch == "/" and nxt == "/":
            current.append(ch)
            current.append(nxt)
            in_line_comment = True
            i += 2
            continue

        if not in_string and not in_char and ch == "/" and nxt == "*":
            current.append(ch)
            current.append(nxt)
            in_block_comment = True
            i += 2
            continue

        if ch == '"' and not in_char and not escape:
            in_string = not in_string
        elif ch == "'" and not in_string and not escape:
            in_char = not in_char

        escape = ch == "\\" and not escape
        if ch != "\\":
            escape = False

        if in_string or in_char:
            current.append(ch)
            i += 1
            continue

        if ch in "\r\n":
            emit()
            i += 1
            continue

        if ch == "{":
            current.append(ch)
            emit()
            i += 1
            continue

        if ch == "}":
            emit()
            current.append(ch)
            emit()
            i += 1
            continue

        if ch == ";":
            current.append(ch)
            emit()
            i += 1
            continue

        current.append(ch)
        i += 1

    emit()
    return _join_else_lines(lines)


def _normalize_brace_spacing(text: str) -> str:
    if text.endswith("{") and len(text) > 1 and not text[-2].isspace():
        return f"{text[:-1].rstrip()} {{"
    return text


def _join_else_lines(lines: list[str]) -> list[str]:
    joined: list[str] = []
    for line in lines:
        if line.startswith("else") and joined and joined[-1] == "}":
            joined.append(line)
        else:
            joined.append(line)
    return joined
