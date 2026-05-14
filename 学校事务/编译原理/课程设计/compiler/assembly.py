from typing import Dict, Iterable, List, Tuple

from .models import ASTNode


Quad = Tuple[object, object, object, object]

ARG_REGISTERS = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
MASM_ARG_REGISTERS = ["ax", "bx", "cx", "dx"]
ARITHMETIC_OPS = {"+", "-", "*", "/", "%"}
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

    def param_name(value: str) -> str:
        parts = value.split()
        return parts[-1] if len(parts) > 1 else ""

    def walk(node: ASTNode) -> None:
        if node.name == "FunctionDef":
            function_name = _decl_name(node.value or "")
            param_names = []
            for child in node.children:
                if child.name == "Param":
                    extracted = param_name(child.value or "")
                    if extracted:
                        param_names.append(extracted)
            params[function_name] = param_names
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
        self.global_initializers, self.functions = self._split_functions()

    def generate(self) -> str:
        if not self.quads:
            return ""

        lines = [
            "assume cs:code,ds:data,ss:stack,es:extended",
            "extended segment",
            "  db 1024 dup (0)",
            "extended ends",
            "stack segment",
            "  db 1024 dup (0)",
            "stack ends",
            "dispmsg macro message",
            "  lea dx, message",
            "  mov ah, 9",
            "  int 21h",
            "endm",
            "data segment",
            "  _buff_p db 256 dup (24h)",
            "  _buff_s db 256 dup (0)",
            "  _msg_p db 0ah,'Output:',0",
            "  _msg_s db 0ah,'Input:',0",
            "  next_row db 0dh,0ah,'$'",
            "  error db 'input error, please re-enter: ','$'",
        ]
        for name, value in self.global_initializers.items():
            lines.append(f"  {name} dw {value}")
        lines.extend([
            "data ends",
            "code segment",
            "start:",
            "    mov ax,extended",
            "    mov es,ax",
            "    mov ax,stack",
            "    mov ss,ax",
            "    mov sp,1024",
            "    mov bp,sp",
            "    mov ax,data",
            "    mov ds,ax",
            "",
        ])

        for function in self.functions:
            lines.extend(Masm16FunctionEmitter(function, self.function_params.get(function.name, []), self.global_initializers).emit())
            lines.append("")

        lines.extend(MASM16_RUNTIME.rstrip().splitlines())
        lines.extend(["code ends", "end start"])
        return "\n".join(lines).rstrip() + "\n"

    def _split_functions(self) -> Tuple[Dict[str, object], List["FunctionQuads"]]:
        global_initializers: Dict[str, object] = {}
        functions: List[FunctionQuads] = []
        current_name = ""
        current_start = 0
        current_quads: List[Tuple[int, Quad]] = []

        for index, quad in enumerate(self.quads):
            if _is_function_label(quad):
                if current_quads:
                    functions.append(FunctionQuads(current_name, current_start, current_quads))
                current_name = str(quad[0])
                current_start = index
                current_quads = [(index, quad)]
            elif not current_name:
                op, arg1, _arg2, result = quad
                if op == "=" and _is_variable(result):
                    global_initializers[str(result)] = arg1
            else:
                current_quads.append((index, quad))

        if current_quads:
            functions.append(FunctionQuads(current_name, current_start, current_quads))
        return global_initializers, functions


class Masm16FunctionEmitter:
    def __init__(self, function: "FunctionQuads", params: List[str], globals_: Dict[str, object] | None = None):
        self.function = function
        self.params = params
        self.globals = globals_ or {}
        self.assembly_name = function.name
        self.variables = self._collect_variables()
        self.offsets = {name: (index + 1) * 2 for index, name in enumerate(self.variables)}
        self.param_offsets = {name: 4 + index * 2 for index, name in enumerate(self.params)}
        self.pending_params: List[object] = []
        self.lines: List[str] = []
        self.return_emitted = False

    def emit(self) -> List[str]:
        local_size = len(self.variables) * 2
        self.lines = [
            f"{self.assembly_name}:",
            "    PUSH BP",
            "    MOV BP,SP",
        ]
        if local_size:
            self.lines.append(f"    SUB SP,{local_size}")

        label_targets = self._label_targets()
        for index, quad in self.function.quads:
            op, arg1, arg2, result = quad
            if _is_function_label(quad):
                continue
            if index in label_targets:
                self.lines.append(f"_{index}:")
            self._emit_quad(op, arg1, arg2, result)

        if not self.return_emitted:
            self.lines.append("    MOV AX,0")
            self._emit_return()
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
            self.lines.append(f"    CMP AX,{self._operand(arg2)}")
            self.lines.append(f"    {JUMP_OPS[str(op)].upper()} _{result}")
        elif op == "J":
            self.lines.append(f"    JMP far ptr _{result}")
        elif op == "para":
            self.pending_params.append(arg1)
        elif op == "call":
            self._emit_call(str(arg1), result)
        elif op in {"ret", "return"}:
            value = 0 if result == "_" else result
            self._load("ax", value)
            self._emit_return()
        elif op == "sys" and self.function.name == "main" and not self.return_emitted:
            self.lines.append("    MOV AX,0")
            self._emit_return()

    def _emit_arithmetic(self, op: str, arg1, arg2, result) -> None:
        self._load("ax", arg1)
        if op == "-" and arg2 == "_":
            self.lines.append("    NEG AX")
        elif op == "+":
            self.lines.append(f"    ADD AX,{self._operand(arg2)}")
        elif op == "-":
            self.lines.append(f"    SUB AX,{self._operand(arg2)}")
        elif op == "*":
            self._load("bx", arg2)
            self.lines.append("    MUL BX")
        elif op == "/":
            self._load("bx", arg2)
            self.lines.append("    CWD")
            self.lines.append("    IDIV BX")
        elif op == "%":
            self._load("bx", arg2)
            self.lines.append("    CWD")
            self.lines.append("    IDIV BX")
            self.lines.append("    MOV AX,DX")
        self._store(result, "ax")

    def _emit_relation(self, op: str, arg1, arg2, result) -> None:
        true_label = self._internal_label("rel_true")
        end_label = self._internal_label("rel_end")
        jump = JUMP_OPS[f"J{op}"]
        self._load("ax", arg1)
        self.lines.append(f"    CMP AX,{self._operand(arg2)}")
        self.lines.append(f"    {jump.upper()} {true_label}")
        self.lines.append("    MOV AX,0")
        self.lines.append(f"    JMP {end_label}")
        self.lines.append(f"{true_label}:")
        self.lines.append("    MOV AX,1")
        self.lines.append(f"{end_label}:")
        self._store(result, "ax")

    def _emit_logical(self, op: str, arg1, arg2, result) -> None:
        true_label = self._internal_label("logic_true")
        end_label = self._internal_label("logic_end")
        self._load("ax", arg1)
        self.lines.append("    CMP AX,0")
        if op == "&&":
            self.lines.append(f"    JE {end_label}")
            self._load("ax", arg2)
            self.lines.append("    CMP AX,0")
            self.lines.append(f"    JNE {true_label}")
            self.lines.append(f"    JMP {end_label}")
        else:
            self.lines.append(f"    JNE {true_label}")
            self._load("ax", arg2)
            self.lines.append("    CMP AX,0")
            self.lines.append(f"    JNE {true_label}")
        self.lines.append("    MOV AX,0")
        self.lines.append(f"    JMP {end_label}_store")
        self.lines.append(f"{true_label}:")
        self.lines.append("    MOV AX,1")
        self.lines.append(f"{end_label}_store:")
        self._store(result, "ax")
        self.lines.append(f"{end_label}:")

    def _emit_call(self, function_name: str, result) -> None:
        if function_name == "read":
            self.pending_params = []
            self.lines.append("    CALL read")
            self._store(result, "ax")
            return
        if function_name == "write":
            if self.pending_params:
                value = self.pending_params[0]
                if isinstance(value, str) and not _is_integer(value) and value not in self.offsets and value not in self.globals:
                    self.lines.append(f"    ; builtin write(): string {value!r}")
                else:
                    self._load("ax", value)
                    self.lines.append("    PUSH AX")
            self.pending_params = []
            self.lines.append("    CALL write")
            self._store(result, "ax")
            return
        for value in reversed(self.pending_params):
            self._load("ax", value)
            self.lines.append("    PUSH AX")
        self.pending_params = []
        self.lines.append(f"    CALL {function_name}")
        self._store(result, "ax")

    def _emit_return(self) -> None:
        if self.function.name == "main":
            self.lines.append("    mov ah,4ch")
            self.lines.append("    int 21h")
        else:
            self.lines.append("    MOV SP,BP")
            self.lines.append("    POP BP")
            self.lines.append("    RET")
        self.return_emitted = True

    def _load(self, register: str, value) -> None:
        if _is_integer(value):
            self.lines.append(f"    MOV {register.upper()},{value}")
        elif value == "_":
            self.lines.append(f"    MOV {register.upper()},0")
        else:
            self.lines.append(f"    MOV {register.upper()},{self._operand(value)}")

    def _store(self, target, register: str) -> None:
        if target == "_":
            return
        self.lines.append(f"    MOV {self._operand(target)},{register.upper()}")

    def _operand(self, value) -> str:
        if _is_integer(value):
            return str(value)
        name = str(value)
        if name in self.globals:
            return name
        if name in self.param_offsets:
            return f"ss:[bp+{self.param_offsets[name]}]"
        if name not in self.offsets:
            self.offsets[name] = (len(self.offsets) + 1) * 2
        return f"ss:[bp-{self.offsets[name]}]"

    def _label_targets(self) -> set[int]:
        return {int(result) for _index, (op, _arg1, _arg2, result) in self.function.quads if str(op).startswith("J") and isinstance(result, int)}

    def _internal_label(self, kind: str) -> str:
        return f"{self.assembly_name}_{kind}_{len(self.lines)}"

    def _collect_variables(self) -> List[str]:
        ordered: List[str] = []
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
                if value in self.globals:
                    continue
                if value in self.params:
                    continue
                _append_name(ordered, value)
        return ordered


MASM16_RUNTIME = """
read proc near
    push bp
    mov bp, sp
    mov bx,offset _msg_s
    call _print
    push bx
    push cx
    push dx
proc_pre_start:
    xor ax, ax
    xor bx, bx
    xor cx, cx
    xor dx, dx
proc_judge_sign:
    mov ah, 1
    int 21h
    cmp al, '-'
    jne proc_next
    mov dx, 0ffffh
    jmp proc_digit_in
proc_next:
    cmp al, 30h
    jb proc_unexpected
    cmp al, 39h
    ja proc_unexpected
    sub al, 30h
    shl bx, 1
    mov cx, bx
    shl bx, 1
    shl bx, 1
    add bx, cx
    add bl, al
    adc bh, 0
proc_digit_in:
    mov ah, 1
    int 21h
    jmp proc_next
proc_save:
    cmp dx, 0ffffh
    jne proc_result_save
    neg bx
proc_result_save:
    mov ax, bx
    jmp proc_input_done
proc_unexpected:
    cmp al, 0dh
    je proc_save
    dispmsg next_row
    dispmsg error
    jmp proc_pre_start
proc_input_done:
    pop dx
    pop cx
    pop bx
    pop bp
    ret
read endp

write proc near
    push bp
    mov bp, sp
    push ax
    push bx
    push cx
    push dx
    mov bx,offset _msg_p
    call _print
    xor cx, cx
    mov bx, [bp+4]
    test bx, 8000h
    jz proc_nonneg
    neg bx
    mov dl,'-'
    mov ah, 2
    int 21h
proc_nonneg:
    mov ax, bx
    cwd
    mov bx, 10
proc_div_again:
    xor dx, dx
    div bx
    add dl, 30h
    push dx
    inc cx
    cmp ax, 0
    jne proc_div_again
proc_digit_out:
    pop dx
    mov ah, 2
    int 21h
    loop proc_digit_out
proc_output_done:
    pop dx
    pop cx
    pop bx
    pop ax
    pop bp
    ret 2
write endp

_print:
    mov si,0
    mov di,offset _buff_p
_p_lp_1:
    mov al,ds:[bx+si]
    cmp al,0
    je _p_brk_1
    mov ds:[di],al
    inc si
    inc di
    jmp short _p_lp_1
_p_brk_1:
    mov dx,offset _buff_p
    mov ah,09h
    int 21h
    mov cx,si
    mov di,offset _buff_p
_p_lp_2:
    mov al,24h
    mov ds:[di],al
    inc di
    loop _p_lp_2
    ret
"""


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
    return isinstance(value, str) and value != "_" and not _is_integer(value) and "\n" not in value and " " not in value and not any(ch in value for ch in '：:,.!?()[]{}')


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
