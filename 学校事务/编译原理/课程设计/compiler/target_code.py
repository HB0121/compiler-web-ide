from typing import Iterable, List, Set, Tuple


Quad = Tuple[object, object, object, object]


ARITHMETIC_OPS = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "%": "MOD",
}

JUMP_OPS = {
    "J>": "JG",
    "J<": "JL",
    "J>=": "JGE",
    "J<=": "JLE",
    "J==": "JE",
    "J!=": "JNE",
}

SKIPPED_OPS = {"para", "call"}


def quads_to_target_code(quads: Iterable[Quad]) -> str:
    converter = TargetCodeConverter(list(quads))
    return converter.convert()


class TargetCodeConverter:
    def __init__(self, quads: List[Quad]):
        self.quads = quads

    def convert(self) -> str:
        lines: List[str] = []
        labels = self._label_targets()

        for index, (op, arg1, arg2, result) in enumerate(self.quads):
            if index in labels:
                lines.append(f"L{index}:")

            if self._is_function_label(op, arg1, arg2, result):
                lines.append(f"FUNC {op}")
                continue

            if op == "=":
                lines.append(f"MOV {result}, {arg1}")
                continue

            if op in ARITHMETIC_OPS:
                lines.append(f"LOAD R1, {arg1}")
                lines.append(f"{ARITHMETIC_OPS[str(op)]} R1, {arg2}")
                lines.append(f"STORE {result}, R1")
                continue

            if op in JUMP_OPS:
                lines.append(f"{JUMP_OPS[str(op)]} {arg1}, {arg2}, L{result}")
                continue

            if op == "J":
                lines.append(f"JMP L{result}")
                continue

            if op in {"ret", "return"}:
                value = "0" if result == "_" else result
                lines.append(f"RET {value}")
                continue

            if op == "sys":
                lines.append("END")
                continue

            if op in SKIPPED_OPS:
                lines.append(f"; {op} {arg1} {arg2} {result}")

        return "\n".join(lines) + ("\n" if lines else "")

    def _label_targets(self) -> Set[int]:
        labels: Set[int] = set()
        for op, _arg1, _arg2, result in self.quads:
            if str(op).startswith("J") and isinstance(result, int):
                labels.add(result)
        return labels

    def _is_function_label(self, op, arg1, arg2, result) -> bool:
        return (
            isinstance(op, str)
            and arg1 == "_"
            and arg2 == "_"
            and result == "_"
            and op not in {"J", "sys", "ret", "return"}
        )
