import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


Quad = Tuple[object, object, object, object]


ARITHMETIC_OPS = {
    "+": "add",
    "-": "sub",
    "*": "mul",
    "/": "sdiv",
    "%": "srem",
}

COMPARE_PREDICATES = {
    ">": "sgt",
    "<": "slt",
    ">=": "sge",
    "<=": "sle",
    "==": "eq",
    "!=": "ne",
    "J>": "sgt",
    "J<": "slt",
    "J>=": "sge",
    "J<=": "sle",
    "J==": "eq",
    "J!=": "ne",
}

TERMINATOR_PREFIXES = ("br ", "ret ")


class LLVMIRConverter:
    def __init__(self, quads: Iterable[Quad]):
        self.source_quads = [tuple(quad) for quad in quads]
        self.active_indices = self._active_indices()
        self.active_set = set(self.active_indices)
        self.variables = self._collect_variables()
        self.label_targets = self._jump_targets()
        self.value_count = 1
        self.cmp_count = 1
        self.lines: List[str] = []
        self.pending_params: List[str] = []
        self.uses_printf = False

    def convert(self) -> str:
        body = self._convert_body()
        header = []
        if self.uses_printf:
            header.extend([
                '@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\\0A\\00"',
                "declare i32 @printf(i8*, ...)",
                "",
            ])
        return "\n".join(header + body) + "\n"

    def _convert_body(self) -> List[str]:
        self.lines = ["define i32 @main() {", "entry:"]
        for name in sorted(self.variables):
            self.lines.append(f"  %{name} = alloca i32")

        position = 0
        while position < len(self.active_indices):
            index = self.active_indices[position]
            if index in self.label_targets:
                self._start_label(index)

            op, arg1, arg2, result = self.source_quads[index]
            if self._is_function_label(op, arg1, arg2, result):
                position += 1
                continue

            if op == "=":
                value = self._load_value(arg1)
                if self._is_variable(result):
                    self.lines.append(f"  store i32 {value}, i32* %{result}")
                position += 1
                continue

            if op == "=[]":
                # First-stage engineering backend does not lower arrays yet. Keep
                # the generated IR valid by treating unsupported array reads as 0.
                if self._is_temp(str(result)):
                    self.lines.append(f"  %{result} = add i32 0, 0")
                elif self._is_variable(result):
                    self.lines.append(f"  store i32 0, i32* %{result}")
                position += 1
                continue

            if op == "[]=":
                position += 1
                continue

            if op in ARITHMETIC_OPS:
                left = self._load_value(arg1)
                right = self._load_value(arg2)
                self.lines.append(f"  %{result} = {ARITHMETIC_OPS[str(op)]} i32 {left}, {right}")
                position += 1
                continue

            if op in COMPARE_PREDICATES and not str(op).startswith("J"):
                left = self._load_value(arg1)
                right = self._load_value(arg2)
                cmp_name = f"%cmp{self.cmp_count}"
                self.cmp_count += 1
                self.lines.append(f"  {cmp_name} = icmp {COMPARE_PREDICATES[str(op)]} i32 {left}, {right}")
                self.lines.append(f"  %{result} = zext i1 {cmp_name} to i32")
                position += 1
                continue

            if op in {"&&", "||"}:
                left = self._bool_value(arg1)
                right = self._bool_value(arg2)
                op_name = "and" if op == "&&" else "or"
                bool_name = f"%cmp{self.cmp_count}"
                self.cmp_count += 1
                self.lines.append(f"  {bool_name} = {op_name} i1 {left}, {right}")
                self.lines.append(f"  %{result} = zext i1 {bool_name} to i32")
                position += 1
                continue

            if op == "!":
                value = self._bool_value(arg1)
                bool_name = f"%cmp{self.cmp_count}"
                self.cmp_count += 1
                self.lines.append(f"  {bool_name} = xor i1 {value}, true")
                self.lines.append(f"  %{result} = zext i1 {bool_name} to i32")
                position += 1
                continue

            if op == "neg":
                value = self._load_value(arg1)
                self.lines.append(f"  %{result} = sub i32 0, {value}")
                position += 1
                continue

            if op in COMPARE_PREDICATES and str(op).startswith("J"):
                left = self._load_value(arg1)
                right = self._load_value(arg2)
                cmp_name = f"%cmp{self.cmp_count}"
                self.cmp_count += 1
                false_target = self._paired_false_target(index)
                self.lines.append(f"  {cmp_name} = icmp {COMPARE_PREDICATES[str(op)]} i32 {left}, {right}")
                self.lines.append(f"  br i1 {cmp_name}, label %L{result}, label %L{false_target}")
                if position + 1 < len(self.active_indices) and self.active_indices[position + 1] == index + 1 and self.source_quads[index + 1][0] == "J":
                    position += 2
                else:
                    position += 1
                continue

            if op == "J":
                self.lines.append(f"  br label %L{result}")
                position += 1
                continue

            if op == "para":
                self.pending_params.append(self._load_value(arg1))
                position += 1
                continue

            if op == "call":
                self._emit_call(str(arg1), result)
                position += 1
                continue

            if op in {"ret", "return"}:
                value = "0" if result == "_" else self._load_value(result)
                self.lines.append(f"  ret i32 {value}")
                position += 1
                continue

            if op == "sys":
                if not self._last_is_terminator():
                    self.lines.append("  ret i32 0")
                position += 1
                continue

            position += 1

        if not self._last_is_terminator():
            self.lines.append("  ret i32 0")
        self.lines.append("}")
        return self.lines

    def _emit_call(self, name: str, result) -> None:
        if name == "write":
            self.uses_printf = True
            value = self.pending_params[-1] if self.pending_params else "0"
            self.lines.append(
                "  call i32 (i8*, ...) @printf("
                "i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.fmt_int, i32 0, i32 0), "
                f"i32 {value})"
            )
            if self._is_temp(str(result)):
                self.lines.append(f"  %{result} = add i32 0, 0")
            elif self._is_variable(result):
                self.lines.append(f"  store i32 0, i32* %{result}")
            self.pending_params = []
            return

        if name == "read":
            if self._is_temp(str(result)):
                self.lines.append(f"  %{result} = add i32 0, 0")
            elif self._is_variable(result):
                self.lines.append(f"  store i32 0, i32* %{result}")
            self.pending_params = []
            return

        # First-stage support for user calls keeps IR valid and deterministic.
        if self._is_temp(str(result)):
            self.lines.append(f"  %{result} = add i32 0, 0")
        elif self._is_variable(result):
            self.lines.append(f"  store i32 0, i32* %{result}")
        self.pending_params = []

    def _start_label(self, index: int) -> None:
        if not self._last_is_terminator():
            self.lines.append(f"  br label %L{index}")
        self.lines.append(f"L{index}:")

    def _last_is_terminator(self) -> bool:
        return bool(self.lines and self.lines[-1].strip().startswith(TERMINATOR_PREFIXES))

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
            self.lines.append(f"  {value_name} = load i32, i32* %{text}")
            return value_name
        return "0"

    def _bool_value(self, item) -> str:
        value = self._load_value(item)
        if value in {"0", "false"}:
            return "false"
        if value in {"1", "true"}:
            return "true"
        cmp_name = f"%cmp{self.cmp_count}"
        self.cmp_count += 1
        self.lines.append(f"  {cmp_name} = icmp ne i32 {value}, 0")
        return cmp_name

    def _collect_variables(self) -> Set[str]:
        variables: Set[str] = set()
        for index in self.active_indices:
            op, arg1, arg2, result = self.source_quads[index]
            items = (arg1, arg2, result)
            if op == "call":
                items = (result,)
            if op == "para":
                items = (arg1,)
            for item in items:
                if self._is_variable(item) and str(item) not in {"write", "read"}:
                    variables.add(str(item))
        return variables

    def _jump_targets(self) -> Set[int]:
        targets: Set[int] = set()
        for index in self.active_indices:
            op, _arg1, _arg2, result = self.source_quads[index]
            if str(op).startswith("J") and isinstance(result, int) and result in self.active_set:
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


def verify_llvm_ir(llvm_ir: str) -> str:
    internal_errors = _internal_verify(llvm_ir)
    lines = ["LLVM Verify", f"Internal verifier: {'PASS' if not internal_errors else 'FAIL'}"]
    if internal_errors:
        lines.append("Internal errors:")
        lines.extend(f"- {error}" for error in internal_errors)
    lines.extend(_external_verify(llvm_ir))
    return "\n".join(lines) + "\n"


def _internal_verify(llvm_ir: str) -> List[str]:
    errors: List[str] = []
    all_lines = [line.rstrip() for line in llvm_ir.splitlines() if line.strip()]
    function_start = next((index for index, line in enumerate(all_lines) if line.startswith("define i32 @main()")), 0)
    lines = all_lines[function_start:]
    if not any(line.startswith("define i32 @main()") for line in lines):
        errors.append("missing define i32 @main()")
    labels = {line[:-1] for line in lines if line.endswith(":")}
    targets = []
    for line in lines:
        stripped = line.strip()
        for part in stripped.replace(",", " ").split():
            if part.startswith("%L"):
                targets.append(part[1:])
    missing = sorted({target for target in targets if target not in labels})
    if missing:
        errors.append(f"missing labels: {', '.join(missing)}")
    for index, line in enumerate(lines[:-1]):
        if line.endswith(":"):
            continue
        next_line = lines[index + 1]
        if next_line.endswith(":") and not line.startswith("define ") and not line.strip().startswith(TERMINATOR_PREFIXES):
            errors.append(f"block before {next_line[:-1]} has no terminator")
    if not any(line.strip().startswith("ret ") for line in lines):
        errors.append("missing ret instruction")
    return errors


def _external_verify(llvm_ir: str) -> List[str]:
    llvm_as = shutil.which("llvm-as")
    lli = shutil.which("lli")
    clang = shutil.which("clang")
    lines = ["External tools:"]
    if llvm_as is None:
        lines.append("- llvm-as: not found")
    if lli is None:
        lines.append("- lli: not found")
    if clang is None:
        lines.append("- clang: not found")
    lines.extend([
        "Manual commands:",
        "  llvm-as outputs/llvm_ir.ll -o outputs/llvm_ir.bc",
        "  lli outputs/llvm_ir.ll",
        "  clang -c outputs/llvm_ir.ll -o outputs/llvm_ir.obj",
        "  clang outputs/llvm_ir.ll -o outputs/llvm_ir.exe",
        "  outputs\\llvm_ir.exe",
    ])
    if llvm_as is None and clang is None:
        return lines

    with tempfile.TemporaryDirectory() as temp_dir:
        ll_path = Path(temp_dir) / "output.ll"
        bc_path = Path(temp_dir) / "output.bc"
        obj_path = Path(temp_dir) / "output.obj"
        ll_path.write_text(llvm_ir, encoding="utf-8")
        if llvm_as is not None:
            result = subprocess.run([llvm_as, str(ll_path), "-o", str(bc_path)], capture_output=True, text=True)
            lines.append(f"- llvm-as: {'PASS' if result.returncode == 0 else 'FAIL'}")
            if result.stderr.strip():
                lines.append(result.stderr.strip())
            if lli is not None and result.returncode == 0:
                run_result = subprocess.run([lli, str(ll_path)], capture_output=True, text=True)
                lines.append(f"- lli: {'PASS' if run_result.returncode == 0 else 'FAIL'}")
                if run_result.stdout.strip():
                    lines.append(f"lli stdout: {run_result.stdout.strip()}")
                if run_result.stderr.strip():
                    lines.append(f"lli stderr: {run_result.stderr.strip()}")
        if clang is not None:
            clang_result = subprocess.run([clang, "-c", str(ll_path), "-o", str(obj_path)], capture_output=True, text=True)
            lines.append(f"- clang -c: {'PASS' if clang_result.returncode == 0 else 'FAIL'}")
            if clang_result.stderr.strip():
                lines.append(clang_result.stderr.strip())
    return lines
