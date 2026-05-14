from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


Quad = Tuple[object, object, object, object]


@dataclass
class ExecutionResult:
    return_value: object
    variables: Dict[str, object]
    trace: List[str]

    def format(self) -> str:
        lines = [
            "Execution Result",
            "Item | Value | Meaning",
            "--- | --- | ---",
            f"return_value | {self._cell(self.return_value)} | 程序最终返回值",
            "",
            "Variables",
            "Name | Value",
            "--- | ---",
        ]
        for name in sorted(self.variables):
            lines.append(f"{self._cell(name)} | {self._cell(self.variables[name])}")
        lines.extend([
            "",
            "Execution Trace",
            "Step | Quad / Event | Meaning",
            "--- | --- | ---",
        ])
        for step, item in enumerate(self.trace, start=1):
            lines.append(f"{step} | {self._cell(item)} | {self._cell(self._explain_trace_item(item))}")

        warnings = [item for item in self.trace if item.startswith("runtime warning") or item.startswith("stopped:")]
        lines.extend(["", "Runtime Warnings", "Warning", "---"])
        if warnings:
            lines.extend(self._cell(item) for item in warnings)
        else:
            lines.append("None")
        return "\n".join(lines) + "\n"

    def _explain_trace_item(self, item: str) -> str:
        if item.startswith("builtin read"):
            return "模拟内置输入函数 read，默认读入 0"
        if item.startswith("builtin write"):
            return "模拟内置输出函数 write"
        if item.startswith("call "):
            return "调用用户自定义函数"
        if item.startswith("runtime warning"):
            return "解释执行阶段的运行时警告"
        if item.startswith("stopped:"):
            return "执行保护停止，通常用于避免死循环"
        quad = self._trace_quad(item)
        if quad is None:
            return "执行事件"
        op, arg1, arg2, result = quad
        if op == "=":
            return f"{result} = {arg1}"
        if op == "=[]":
            return f"{result} = {arg1}[{arg2}]"
        if op == "[]=":
            return f"{result}[{arg2}] = {arg1}"
        if op in {"+", "-", "*", "/", "%", ">", "<", ">=", "<=", "==", "!=", "&&", "||"}:
            return f"{result} = {arg1} {op} {arg2}"
        if op in {"!", "neg"}:
            return f"{result} = {op}{arg1}"
        if op == "para":
            return f"准备函数参数 {arg1}"
        if op == "call":
            return f"调用函数 {arg1}，结果保存到 {result}"
        if op == "J":
            return f"无条件跳转到四元式 {result}"
        if str(op).startswith("J"):
            return f"条件成立时跳转到四元式 {result}"
        if op in {"ret", "return"}:
            return f"返回 {result}"
        if op == "sys":
            return "程序结束"
        return f"进入函数或标签 {op}"

    def _trace_quad(self, item: str) -> Optional[Quad]:
        if "(" not in item or ")" not in item:
            return None
        content = item[item.find("(") + 1 : item.rfind(")")]
        parts = [part.strip() for part in content.split(",")]
        if len(parts) != 4:
            return None
        return parts[0], parts[1], parts[2], parts[3]

    def _cell(self, value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")


class QuadInterpreter:
    def __init__(self, quads: List[Quad]):
        self.quads = quads
        self.values: Dict[str, object] = {}
        self.trace: List[str] = []
        self.return_value: object = None
        self.pending_params: List[object] = []
        self.functions = self._collect_functions()

    def run(self) -> ExecutionResult:
        pc = self._entry_point()
        self._run_global_initializers(pc)
        steps = 0
        max_steps = max(1000, len(self.quads) * 100)

        while 0 <= pc < len(self.quads):
            if steps > max_steps:
                self.trace.append("stopped: step limit exceeded")
                break
            steps += 1

            op, arg1, arg2, result = self.quads[pc]
            self.trace.append(f"{pc}: ({op}, {arg1}, {arg2}, {result})")

            if self._is_label(op, arg1, arg2, result):
                pc += 1
                continue

            if op == "sys":
                break

            if op in {"ret", "return"}:
                self.return_value = None if result == "_" else self._value(result, self.values)
                break

            if op == "=":
                self.values[str(result)] = self._value(arg1, self.values)
                pc += 1
                continue

            if op == "=[]":
                index = self._value(arg2, self.values)
                self.values[str(result)] = self.values.get(f"{arg1}[{index}]", 0)
                pc += 1
                continue

            if op == "[]=":
                index = self._value(arg2, self.values)
                self.values[f"{result}[{index}]"] = self._value(arg1, self.values)
                pc += 1
                continue

            if op in {"+", "-", "*", "/", "%", ">", "<", ">=", "<=", "==", "!=", "&&", "||"}:
                self.values[str(result)] = self._apply_binary(str(op), self._value(arg1, self.values), self._value(arg2, self.values))
                pc += 1
                continue

            if op in {"!", "neg"}:
                value = self._value(arg1, self.values)
                self.values[str(result)] = int(not bool(value)) if op == "!" else -value
                pc += 1
                continue

            if str(op).startswith("J") and op != "J":
                pc = self._jump_target(result, pc + 1) if self._jump_condition(str(op)[1:], self._value(arg1, self.values), self._value(arg2, self.values)) else pc + 1
                continue

            if op == "J":
                pc = self._jump_target(result, pc + 1)
                continue

            if op == "para":
                self.pending_params.append(self._value(arg1, self.values))
                pc += 1
                continue

            if op == "call":
                call_result = self._call_function(str(arg1), self.pending_params)
                self.pending_params = []
                if result != "_":
                    self.values[str(result)] = 0 if call_result is None else call_result
                pc += 1
                continue

            pc += 1

        return ExecutionResult(self.return_value, dict(self.values), list(self.trace))

    def _run_global_initializers(self, entry_point: int) -> None:
        for index in range(entry_point):
            op, arg1, arg2, result = self.quads[index]
            if self._is_label(op, arg1, arg2, result):
                break
            if op == "=":
                self.values[str(result)] = self._value(arg1, self.values)
                self.trace.append(f"{index}: global ({op}, {arg1}, {arg2}, {result})")

    def _entry_point(self) -> int:
        for index, quad in enumerate(self.quads):
            if quad[0] == "main":
                return index + 1
        return 0

    def _call_function(self, name: str, args: List[object]):
        if name == "read":
            self.trace.append("builtin read() -> 0")
            return 0
        if name == "write":
            value = args[0] if args else 0
            self.trace.append(f"builtin write({value})")
            return None
        if name not in self.functions:
            return 0
        start, end = self.functions[name]
        params = self._infer_params(start, end)
        local_values = dict(self.values)
        for param_name, value in zip(params, args):
            local_values[param_name] = value
        self.trace.append(f"call {name}({', '.join(str(arg) for arg in args)})")
        return self._execute_function_body(start, end, local_values)

    def _execute_function_body(self, start: int, end: int, values: Dict[str, object]):
        pc = start
        steps = 0
        max_steps = max(1000, len(self.quads) * 100)

        while start <= pc < end:
            if steps > max_steps:
                self.trace.append(f"stopped: function step limit exceeded at {pc}")
                return 0
            steps += 1

            op, arg1, arg2, result = self.quads[pc]
            self.trace.append(f"{pc}: fn ({op}, {arg1}, {arg2}, {result})")

            if op in {"ret", "return"}:
                return None if result == "_" else self._value(result, values)

            if op == "=":
                values[str(result)] = self._value(arg1, values)
                pc += 1
                continue

            if op == "=[]":
                index = self._value(arg2, values)
                values[str(result)] = values.get(f"{arg1}[{index}]", 0)
                pc += 1
                continue

            if op == "[]=":
                index = self._value(arg2, values)
                values[f"{result}[{index}]"] = self._value(arg1, values)
                pc += 1
                continue

            if op in {"+", "-", "*", "/", "%", ">", "<", ">=", "<=", "==", "!=", "&&", "||"}:
                values[str(result)] = self._apply_binary(str(op), self._value(arg1, values), self._value(arg2, values))
                pc += 1
                continue

            if op in {"!", "neg"}:
                value = self._value(arg1, values)
                values[str(result)] = int(not bool(value)) if op == "!" else -value
                pc += 1
                continue

            if str(op).startswith("J") and op != "J":
                pc = self._jump_target(result, pc + 1) if self._jump_condition(str(op)[1:], self._value(arg1, values), self._value(arg2, values)) else pc + 1
                continue

            if op == "J":
                pc = self._jump_target(result, pc + 1)
                continue

            pc += 1
        return 0

    def _collect_functions(self) -> Dict[str, Tuple[int, int]]:
        functions: Dict[str, Tuple[int, int]] = {}
        labels = [index for index, quad in enumerate(self.quads) if self._is_label(*quad)]
        for position, label_index in enumerate(labels):
            name = str(self.quads[label_index][0])
            if name == "main":
                continue
            end = labels[position + 1] if position + 1 < len(labels) else len(self.quads)
            functions[name] = (label_index + 1, end)
        return functions

    def _infer_params(self, start: int, end: int) -> List[str]:
        params: List[str] = []
        defined = set()
        for pc in range(start, end):
            op, arg1, arg2, result = self.quads[pc]
            for item in self._read_items(op, arg1, arg2, result):
                if self._looks_like_name(item) and item not in defined and item not in self.values and item not in params:
                    params.append(str(item))
            if self._looks_like_name(result) and op not in {"J", "ret", "return", "para", "call"}:
                defined.add(str(result))
        return params

    def _read_items(self, op, arg1, arg2, result) -> List[object]:
        if op in {"ret", "return"}:
            return [result]
        if op == "=":
            return [arg1]
        if op == "=[]":
            return [arg1, arg2]
        if op == "[]=":
            return [arg1, arg2]
        if op in {"+", "-", "*", "/", "%", ">", "<", ">=", "<=", "==", "!=", "&&", "||"} or str(op).startswith("J"):
            return [arg1, arg2]
        if op in {"!", "neg", "para"}:
            return [arg1]
        return []

    def _value(self, item, values: Dict[str, object]):
        if item == "_":
            return 0
        if isinstance(item, (int, float)):
            return item
        text = str(item)
        if text in values:
            return values[text]
        if text.startswith("'") and text.endswith("'") and len(text) >= 2:
            return text[1:-1]
        if text.startswith('"') and text.endswith('"') and len(text) >= 2:
            return text[1:-1]
        try:
            return int(text)
        except ValueError:
            try:
                return float(text)
            except ValueError:
                return 0

    def _apply_binary(self, op: str, left, right):
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                self.trace.append("runtime warning: division by zero, result forced to 0")
                return 0
            return int(left / right)
        if op == "%":
            if right == 0:
                self.trace.append("runtime warning: modulo by zero, result forced to 0")
                return 0
            return int(left % right)
        if op == ">":
            return int(left > right)
        if op == "<":
            return int(left < right)
        if op == ">=":
            return int(left >= right)
        if op == "<=":
            return int(left <= right)
        if op == "==":
            return int(left == right)
        if op == "!=":
            return int(left != right)
        if op == "&&":
            return int(bool(left) and bool(right))
        if op == "||":
            return int(bool(left) or bool(right))
        return 0

    def _jump_condition(self, op: str, left, right) -> bool:
        return bool(self._apply_binary(op, left, right))

    def _jump_target(self, value, fallback: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            self.trace.append(f"runtime warning: invalid jump target {value}, continuing")
            return fallback

    def _is_label(self, op, arg1, arg2, result) -> bool:
        return (
            isinstance(op, str)
            and op not in {"=", "+", "-", "*", "/", "%", ">", "<", ">=", "<=", "==", "!=", "&&", "||", "!", "J", "ret", "return", "sys", "para", "call"}
            and arg1 == "_"
            and arg2 == "_"
            and result == "_"
        )

    def _looks_like_name(self, item) -> bool:
        if not isinstance(item, str) or item == "_":
            return False
        if item.startswith("t") and item[1:].isdigit():
            return False
        try:
            int(item)
            return False
        except ValueError:
            return True


def interpret_quads(quads: List[Quad]) -> ExecutionResult:
    return QuadInterpreter(quads).run()
