from typing import Dict, Iterable, List, Tuple

from .models import ASTNode


Quad = Tuple[object, object, object, object]

ARG_REGISTERS = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
MASM_ARG_REGISTERS = ["ax", "bx", "cx", "dx"]
ARITHMETIC_OPS = {"+", "-", "*", "/"}
RELATION_OPS = {
    ">": "setg",
    "<": "setl",
    ">=": "setge",
    "<=": "setle",
    "==": "sete",
    "!=": "setne",
}
JUMP_OPS = {
    "J>": "jg",
    "J<": "jl",
    "J>=": "jge",
    "J<=": "jle",
    "J==": "je",
    "J!=": "jne",
}


def quads_to_nasm_x86_64(quads: Iterable[Quad], function_params: Dict[str, List[str]] | None = None) -> str:
    return NasmX86Generator(list(quads), function_params or {}).generate()


def quads_to_masm16(quads: Iterable[Quad], function_params: Dict[str, List[str]] | None = None) -> str:
    return Masm16Generator(list(quads), function_params or {}).generate()


def function_params_from_ast(ast: ASTNode | None) -> Dict[str, List[str]]:
    params: Dict[str, List[str]] = {}
    if ast is None:
        return params

    def walk(node: ASTNode) -> None:
        if node.name == "FunctionDef":
            name = _decl_name(node.value or "")
            params[name] = [_decl_name(child.value or "") for child in node.children if child.name == "Param"]
        for child in node.children:
            walk(child)

    walk(ast)
    return params


class NasmX86Generator:
    def __init__(self, quads: List[Quad], function_params: Dict[str, List[str]]):
        self.quads = quads
        self.function_params = function_params
        self.functions = self._split_functions()

    def generate(self) -> str:
        if not self.quads:
            return ""

        lines = [
            "; NASM x86-64 System V assembly",
            "; Assemble on Linux/WSL:",
            "; nasm -f elf64 program.asm -o program.o",
            "; gcc -no-pie program.o -o program",
            "default rel",
            "section .text",
            "global main",
            "",
        ]

        for function in self.functions:
            lines.extend(FunctionEmitter(function, self.function_params.get(function.name, [])).emit())
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _split_functions(self) -> List["FunctionQuads"]:
        functions: List[FunctionQuads] = []
        current_name = "main"
        current_start = 0
        current_quads: List[Tuple[int, Quad]] = []

        for index, quad in enumerate(self.quads):
            if _is_function_label(quad):
                if current_quads:
                    functions.append(FunctionQuads(current_name, current_start, current_quads))
                current_name = str(quad[0])
                current_start = index
                current_quads = [(index, quad)]
            else:
                current_quads.append((index, quad))

        if current_quads:
            functions.append(FunctionQuads(current_name, current_start, current_quads))
        return functions


class Masm16Generator:
    def __init__(self, quads: List[Quad], function_params: Dict[str, List[str]]):
        self.quads = quads
        self.function_params = function_params
        self.functions = self._split_functions()

    def generate(self) -> str:
        if not self.quads:
            return ""

        lines = [
            "; MASM 16-bit DOS assembly",
            "; Assemble with MASM/LINK:",
            "; masm program.asm;",
            "; link program.obj;",
            ".MODEL SMALL",
            ".STACK 100h",
            ".DATA",
            ".CODE",
            "",
        ]

        for function in self.functions:
            lines.extend(Masm16FunctionEmitter(function, self.function_params.get(function.name, [])).emit())
            lines.append("")

        lines.append("END main")
        return "\n".join(lines).rstrip() + "\n"

    def _split_functions(self) -> List["FunctionQuads"]:
        functions: List[FunctionQuads] = []
        current_name = "main"
        current_start = 0
        current_quads: List[Tuple[int, Quad]] = []

        for index, quad in enumerate(self.quads):
            if _is_function_label(quad):
                if current_quads:
                    functions.append(FunctionQuads(current_name, current_start, current_quads))
                current_name = str(quad[0])
                current_start = index
                current_quads = [(index, quad)]
            else:
                current_quads.append((index, quad))

        if current_quads:
            functions.append(FunctionQuads(current_name, current_start, current_quads))
        return functions


class Masm16FunctionEmitter:
    def __init__(self, function: "FunctionQuads", params: List[str]):
        self.function = function
        self.params = params
        self.assembly_name = _masm_function_name(function.name)
        self.variables = self._collect_variables()
        self.offsets = {name: (index + 1) * 2 for index, name in enumerate(self.variables)}
        self.pending_params: List[object] = []
        self.lines: List[str] = []
        self.return_emitted = False

    def emit(self) -> List[str]:
        local_size = len(self.variables) * 2
        self.lines = [
            f"{self.assembly_name} PROC",
            "    push bp",
            "    mov bp, sp",
        ]
        if self.function.name == "main":
            self.lines.extend(["    mov ax, @data", "    mov ds, ax"])
        if local_size:
            self.lines.append(f"    sub sp, {local_size}")

        for index, param in enumerate(self.params[: len(MASM_ARG_REGISTERS)]):
            if param in self.offsets:
                self.lines.append(f"    mov WORD PTR [bp-{self.offsets[param]}], {MASM_ARG_REGISTERS[index]}")

        label_targets = self._label_targets()
        for index, quad in self.function.quads:
            op, arg1, arg2, result = quad
            if _is_function_label(quad):
                continue
            if index in label_targets:
                self.lines.append(f"L{index}:")
            self._emit_quad(op, arg1, arg2, result)

        if not self.return_emitted:
            self.lines.append("    mov ax, 0")
            self._emit_return()
        self.lines.append(f"{self.assembly_name} ENDP")
        return self.lines

    def _emit_quad(self, op, arg1, arg2, result) -> None:
        if self.return_emitted and op in {"ret", "return"} and result == "_":
            return
        if op == "=":
            self._load("ax", arg1)
            self._store(result, "ax")
        elif op in ARITHMETIC_OPS:
            self._emit_arithmetic(str(op), arg1, arg2, result)
        elif op in RELATION_OPS:
            self._emit_relation(str(op), arg1, arg2, result)
        elif op == "!":
            true_label = self._internal_label("not_true")
            end_label = self._internal_label("not_end")
            self._load("ax", arg1)
            self.lines.append("    cmp ax, 0")
            self.lines.append(f"    je {true_label}")
            self.lines.append("    mov ax, 0")
            self.lines.append(f"    jmp {end_label}")
            self.lines.append(f"{true_label}:")
            self.lines.append("    mov ax, 1")
            self.lines.append(f"{end_label}:")
            self._store(result, "ax")
        elif op in {"&&", "||"}:
            self._emit_logical(str(op), arg1, arg2, result)
        elif op in JUMP_OPS:
            self._load("ax", arg1)
            self.lines.append(f"    cmp ax, {self._operand(arg2)}")
            self.lines.append(f"    {JUMP_OPS[str(op)]} L{result}")
        elif op == "J":
            self.lines.append(f"    jmp L{result}")
        elif op == "para":
            self.pending_params.append(arg1)
        elif op == "call":
            self._emit_call(str(arg1), result)
        elif op in {"ret", "return"}:
            value = 0 if result == "_" else result
            self._load("ax", value)
            self._emit_return()
        elif op == "sys" and self.function.name == "main" and not self.return_emitted:
            self.lines.append("    mov ax, 0")
            self._emit_return()

    def _emit_arithmetic(self, op: str, arg1, arg2, result) -> None:
        self._load("ax", arg1)
        if op == "-" and arg2 == "_":
            self.lines.append("    neg ax")
        elif op == "+":
            self.lines.append(f"    add ax, {self._operand(arg2)}")
        elif op == "-":
            self.lines.append(f"    sub ax, {self._operand(arg2)}")
        elif op == "*":
            self._load("bx", arg2)
            self.lines.append("    imul bx")
        elif op == "/":
            self._load("bx", arg2)
            self.lines.append("    cwd")
            self.lines.append("    idiv bx")
        self._store(result, "ax")

    def _emit_relation(self, op: str, arg1, arg2, result) -> None:
        true_label = self._internal_label("rel_true")
        end_label = self._internal_label("rel_end")
        jump = JUMP_OPS[f"J{op}"]
        self._load("ax", arg1)
        self.lines.append(f"    cmp ax, {self._operand(arg2)}")
        self.lines.append(f"    {jump} {true_label}")
        self.lines.append("    mov ax, 0")
        self.lines.append(f"    jmp {end_label}")
        self.lines.append(f"{true_label}:")
        self.lines.append("    mov ax, 1")
        self.lines.append(f"{end_label}:")
        self._store(result, "ax")

    def _emit_logical(self, op: str, arg1, arg2, result) -> None:
        true_label = self._internal_label("logic_true")
        end_label = self._internal_label("logic_end")
        self._load("ax", arg1)
        self.lines.append("    cmp ax, 0")
        if op == "&&":
            self.lines.append(f"    je {end_label}")
            self._load("ax", arg2)
            self.lines.append("    cmp ax, 0")
            self.lines.append(f"    jne {true_label}")
            self.lines.append(f"    jmp {end_label}")
        else:
            self.lines.append(f"    jne {true_label}")
            self._load("ax", arg2)
            self.lines.append("    cmp ax, 0")
            self.lines.append(f"    jne {true_label}")
        self.lines.append("    mov ax, 0")
        self.lines.append(f"    jmp {end_label}_store")
        self.lines.append(f"{true_label}:")
        self.lines.append("    mov ax, 1")
        self.lines.append(f"{end_label}_store:")
        self._store(result, "ax")
        self.lines.append(f"{end_label}:")

    def _emit_call(self, function_name: str, result) -> None:
        for index, value in enumerate(self.pending_params[: len(MASM_ARG_REGISTERS)]):
            self._load(MASM_ARG_REGISTERS[index], value)
        self.pending_params = []
        self.lines.append(f"    call {_masm_function_name(function_name)}")
        self._store(result, "ax")

    def _emit_return(self) -> None:
        if self.function.name == "main":
            self.lines.append("    mov ah, 4Ch")
            self.lines.append("    int 21h")
        else:
            self.lines.append("    mov sp, bp")
            self.lines.append("    pop bp")
            self.lines.append("    ret")
        self.return_emitted = True

    def _load(self, register: str, value) -> None:
        if _is_integer(value):
            self.lines.append(f"    mov {register}, {value}")
        elif value == "_":
            self.lines.append(f"    mov {register}, 0")
        else:
            self.lines.append(f"    mov {register}, {self._operand(value)}")

    def _store(self, target, register: str) -> None:
        if target == "_":
            return
        self.lines.append(f"    mov {self._operand(target)}, {register}")

    def _operand(self, value) -> str:
        if _is_integer(value):
            return str(value)
        name = str(value)
        if name not in self.offsets:
            self.offsets[name] = (len(self.offsets) + 1) * 2
        return f"WORD PTR [bp-{self.offsets[name]}]"

    def _label_targets(self) -> set[int]:
        return {int(result) for _index, (op, _arg1, _arg2, result) in self.function.quads if str(op).startswith("J") and isinstance(result, int)}

    def _internal_label(self, kind: str) -> str:
        return f"{self.assembly_name}_{kind}_{len(self.lines)}"

    def _collect_variables(self) -> List[str]:
        ordered: List[str] = []
        for param in self.params:
            _append_name(ordered, param)
        for _index, (op, arg1, arg2, result) in self.function.quads:
            if _is_function_label((op, arg1, arg2, result)):
                continue
            if op == "call":
                _append_name(ordered, result)
                continue
            if op == "para":
                _append_name(ordered, arg1)
                continue
            for value in (arg1, arg2, result):
                _append_name(ordered, value)
        return ordered


class FunctionQuads:
    def __init__(self, name: str, start: int, quads: List[Tuple[int, Quad]]):
        self.name = name
        self.start = start
        self.quads = quads


class FunctionEmitter:
    def __init__(self, function: FunctionQuads, params: List[str]):
        self.function = function
        self.params = params
        self.variables = self._collect_variables()
        self.offsets = {name: (index + 1) * 8 for index, name in enumerate(self.variables)}
        self.pending_params: List[object] = []
        self.lines: List[str] = []

    def emit(self) -> List[str]:
        stack_size = self._aligned_stack_size()
        self.lines = [
            f"{self.function.name}:",
            "    push rbp",
            "    mov rbp, rsp",
        ]
        if stack_size:
            self.lines.append(f"    sub rsp, {stack_size}")

        for index, param in enumerate(self.params[: len(ARG_REGISTERS)]):
            if param in self.offsets:
                self.lines.append(f"    mov [rbp-{self.offsets[param]}], {ARG_REGISTERS[index]}")

        label_targets = self._label_targets()
        saw_explicit_return = False
        for index, quad in self.function.quads:
            op, arg1, arg2, result = quad
            if _is_function_label(quad):
                continue
            if index in label_targets:
                self.lines.append(f".L{index}:")
            if op == "=":
                self._load("rax", arg1)
                self._store(result, "rax")
            elif op in ARITHMETIC_OPS:
                self._emit_arithmetic(str(op), arg1, arg2, result)
            elif op in RELATION_OPS:
                self._emit_relation(str(op), arg1, arg2, result)
            elif op == "!":
                self._load("rax", arg1)
                self.lines.append("    cmp rax, 0")
                self.lines.append("    sete al")
                self.lines.append("    movzx rax, al")
                self._store(result, "rax")
            elif op == "&&":
                self._emit_logical_and(arg1, arg2, result)
            elif op == "||":
                self._emit_logical_or(arg1, arg2, result)
            elif op in JUMP_OPS:
                self._load("rax", arg1)
                self._compare_rax(arg2)
                self.lines.append(f"    {JUMP_OPS[str(op)]} .L{result}")
            elif op == "J":
                self.lines.append(f"    jmp .L{result}")
            elif op == "para":
                self.pending_params.append(arg1)
            elif op == "call":
                self._emit_call(str(arg1), result)
            elif op in {"ret", "return"}:
                value = 0 if result == "_" else result
                self._load("rax", value)
                self._emit_epilogue()
                saw_explicit_return = True
            elif op == "sys":
                if not saw_explicit_return:
                    self.lines.append("    mov rax, 0")
                    self._emit_epilogue()
                    saw_explicit_return = True

        if not saw_explicit_return:
            self.lines.append("    mov rax, 0")
            self._emit_epilogue()
        return self.lines

    def _emit_arithmetic(self, op: str, arg1, arg2, result) -> None:
        self._load("rax", arg1)
        if op == "-" and arg2 == "_":
            self.lines.append("    neg rax")
        elif op == "+":
            self.lines.append(f"    add rax, {self._operand(arg2)}")
        elif op == "-":
            self.lines.append(f"    sub rax, {self._operand(arg2)}")
        elif op == "*":
            self.lines.append(f"    imul rax, {self._operand(arg2)}")
        elif op == "/":
            self._load("rbx", arg2)
            self.lines.append("    cqo")
            self.lines.append("    idiv rbx")
        self._store(result, "rax")

    def _emit_relation(self, op: str, arg1, arg2, result) -> None:
        self._load("rax", arg1)
        self._compare_rax(arg2)
        self.lines.append(f"    {RELATION_OPS[op]} al")
        self.lines.append("    movzx rax, al")
        self._store(result, "rax")

    def _emit_logical_and(self, arg1, arg2, result) -> None:
        self._load("rax", arg1)
        self.lines.append("    cmp rax, 0")
        self.lines.append("    setne al")
        self.lines.append("    movzx rax, al")
        self._load("rbx", arg2)
        self.lines.append("    cmp rbx, 0")
        self.lines.append("    setne bl")
        self.lines.append("    movzx rbx, bl")
        self.lines.append("    and rax, rbx")
        self._store(result, "rax")

    def _emit_logical_or(self, arg1, arg2, result) -> None:
        self._load("rax", arg1)
        self.lines.append("    cmp rax, 0")
        self.lines.append("    setne al")
        self.lines.append("    movzx rax, al")
        self._load("rbx", arg2)
        self.lines.append("    cmp rbx, 0")
        self.lines.append("    setne bl")
        self.lines.append("    movzx rbx, bl")
        self.lines.append("    or rax, rbx")
        self._store(result, "rax")

    def _emit_call(self, function_name: str, result) -> None:
        for index, value in enumerate(self.pending_params[: len(ARG_REGISTERS)]):
            self._load(ARG_REGISTERS[index], value)
        self.pending_params = []
        self.lines.append(f"    call {function_name}")
        self._store(result, "rax")

    def _compare_rax(self, value) -> None:
        self.lines.append(f"    cmp rax, {self._operand(value)}")

    def _load(self, register: str, value) -> None:
        if _is_integer(value):
            self.lines.append(f"    mov {register}, {value}")
        elif value == "_":
            self.lines.append(f"    mov {register}, 0")
        else:
            self.lines.append(f"    mov {register}, {self._operand(value)}")

    def _store(self, target, register: str) -> None:
        if target == "_":
            return
        self.lines.append(f"    mov {self._operand(target)}, {register}")

    def _operand(self, value) -> str:
        if _is_integer(value):
            return str(value)
        name = str(value)
        if name not in self.offsets:
            self.offsets[name] = (len(self.offsets) + 1) * 8
        return f"[rbp-{self.offsets[name]}]"

    def _emit_epilogue(self) -> None:
        self.lines.append("    leave")
        self.lines.append("    ret")

    def _aligned_stack_size(self) -> int:
        size = len(self.variables) * 8
        return ((size + 15) // 16) * 16

    def _label_targets(self) -> set[int]:
        return {int(result) for _index, (op, _arg1, _arg2, result) in self.function.quads if str(op).startswith("J") and isinstance(result, int)}

    def _collect_variables(self) -> List[str]:
        ordered: List[str] = []
        for param in self.params:
            _append_name(ordered, param)
        for _index, (op, arg1, arg2, result) in self.function.quads:
            if _is_function_label((op, arg1, arg2, result)):
                continue
            if op == "call":
                _append_name(ordered, result)
                continue
            if op == "para":
                _append_name(ordered, arg1)
                continue
            for value in (arg1, arg2, result):
                _append_name(ordered, value)
        return ordered


def _append_name(names: List[str], value) -> None:
    if not _is_variable(value):
        return
    text = str(value)
    if text not in names:
        names.append(text)


def _is_variable(value) -> bool:
    return isinstance(value, str) and value != "_" and not _is_integer(value)


def _is_integer(value) -> bool:
    return isinstance(value, (int, str)) and str(value).lstrip("-").isdigit()


def _masm_function_name(name: str) -> str:
    return "main" if name == "main" else f"fn_{name}"


def _is_function_label(quad: Quad) -> bool:
    op, arg1, arg2, result = quad
    return (
        isinstance(op, str)
        and arg1 == "_"
        and arg2 == "_"
        and result == "_"
        and op not in {"J", "sys", "ret", "return"}
    )


def _decl_name(value: str) -> str:
    parts = value.split()
    return parts[-1].replace(",", "") if parts else ""
