from typing import Dict, Iterable, List, Set, Tuple


Quad = Tuple[object, object, object, object]


ARITHMETIC_OPS = {
    "+": "add",
    "-": "sub",
    "*": "mul",
    "/": "sdiv",
    "%": "srem",
}

JUMP_PREDICATES = {
    "J>": "sgt",
    "J<": "slt",
    "J>=": "sge",
    "J<=": "sle",
    "J==": "eq",
    "J!=": "ne",
}


class LLVMIRConverter:
    def __init__(self, quads: Iterable[Quad]):
        self.source_quads = list(quads)
        self.active_indices = self._active_indices()
        self.value_count = 1
        self.cmp_count = 1
        self.variables = self._collect_variables()
        self.lines: List[str] = []

    def convert(self) -> str:
        self.lines = ["define i32 @main() {", "entry:"]
        for name in sorted(self.variables):
            self.lines.append(f"%{name} = alloca i32")

        label_targets = self._jump_targets()
        position = 0
        while position < len(self.active_indices):
            index = self.active_indices[position]
            if index in label_targets:
                self.lines.append(f"L{index}:")

            op, arg1, arg2, result = self.source_quads[index]
            if self._is_function_label(op, arg1, arg2, result):
                position += 1
                continue

            if op == "=":
                value = self._load_value(arg1)
                if self._is_variable(result):
                    self.lines.append(f"store i32 {value}, ptr %{result}")
                position += 1
                continue

            if op in ARITHMETIC_OPS:
                left = self._load_value(arg1)
                right = self._load_value(arg2)
                self.lines.append(f"%{result} = {ARITHMETIC_OPS[str(op)]} i32 {left}, {right}")
                position += 1
                continue

            if op in JUMP_PREDICATES:
                left = self._load_value(arg1)
                right = self._load_value(arg2)
                cmp_name = f"%cmp{self.cmp_count}"
                self.cmp_count += 1
                false_target = self._paired_false_target(index)
                self.lines.append(f"{cmp_name} = icmp {JUMP_PREDICATES[str(op)]} i32 {left}, {right}")
                self.lines.append(f"br i1 {cmp_name}, label %L{result}, label %L{false_target}")
                if position + 1 < len(self.active_indices) and self.active_indices[position + 1] == index + 1 and self.source_quads[index + 1][0] == "J":
                    position += 2
                else:
                    position += 1
                continue

            if op == "J":
                self.lines.append(f"br label %L{result}")
                position += 1
                continue

            if op in {"ret", "return"}:
                value = "0" if result == "_" else self._load_value(result)
                self.lines.append(f"ret i32 {value}")
                position += 1
                continue

            if op == "sys":
                position += 1
                continue

            if op == "call":
                if self._is_temp(str(result)):
                    self.lines.append(f"%{result} = add i32 0, 0")
                elif self._is_variable(result):
                    self.lines.append(f"store i32 0, ptr %{result}")
                position += 1
                continue

            position += 1

        if not any(line.startswith("ret i32") for line in self.lines):
            self.lines.append("ret i32 0")
        self.lines.append("}")
        return "\n".join(self.lines) + "\n"

    def _collect_variables(self) -> Set[str]:
        variables: Set[str] = set()
        for index in self.active_indices:
            op, arg1, arg2, result = self.source_quads[index]
            items = (result,) if op == "call" else (arg1, arg2, result)
            for item in items:
                if self._is_variable(item):
                    variables.add(str(item))
        return variables

    def _jump_targets(self) -> Set[int]:
        targets: Set[int] = set()
        for index in self.active_indices:
            op, _arg1, _arg2, result = self.source_quads[index]
            if str(op).startswith("J") and isinstance(result, int):
                targets.add(result)
        return targets

    def _paired_false_target(self, index: int) -> int:
        next_index = index + 1
        if next_index < len(self.source_quads) and self.source_quads[next_index][0] == "J":
            return int(self.source_quads[next_index][3])
        return next_index

    def _active_indices(self) -> List[int]:
        main_index = None
        for index, quad in enumerate(self.source_quads):
            if quad[0] == "main" and quad[1] == "_" and quad[2] == "_" and quad[3] == "_":
                main_index = index
                break
        if main_index is None:
            return list(range(len(self.source_quads)))

        active: List[int] = []
        for index in range(main_index):
            quad = self.source_quads[index]
            if self._is_function_label(*quad):
                break
            active.append(index)

        index = main_index + 1
        while index < len(self.source_quads):
            quad = self.source_quads[index]
            if self._is_function_label(*quad):
                break
            active.append(index)
            if quad[0] == "sys":
                break
            index += 1
        return active

    def _load_value(self, item) -> str:
        if item == "_":
            return "0"
        if isinstance(item, int):
            return str(item)
        text = str(item)
        if self._is_integer(text):
            return text
        if self._is_temp(text):
            return f"%{text}"
        if self._is_variable(text):
            value_name = f"%v{self.value_count}"
            self.value_count += 1
            self.lines.append(f"{value_name} = load i32, ptr %{text}")
            return value_name
        return text

    def _is_function_label(self, op, arg1, arg2, result) -> bool:
        return isinstance(op, str) and arg1 == "_" and arg2 == "_" and result == "_" and op not in {"J", "sys", "ret", "return"}

    def _is_variable(self, item) -> bool:
        if not isinstance(item, str):
            return False
        return item != "_" and not self._is_integer(item) and not self._is_temp(item) and item not in {"sys", "ret", "return"}

    def _is_temp(self, item: str) -> bool:
        return item.startswith("t") and item[1:].isdigit()

    def _is_integer(self, item: str) -> bool:
        return item.lstrip("-").isdigit()


def quads_to_llvm_ir(quads: Iterable[Quad]) -> str:
    return LLVMIRConverter(quads).convert()
