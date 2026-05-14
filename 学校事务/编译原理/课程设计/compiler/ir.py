import re
from typing import List, Optional, Tuple

from .models import ASTNode as SharedASTNode


class IRNode:
    pass


class Program(IRNode):
    def __init__(self, nodes):
        self.nodes = nodes


class FuncDef(IRNode):
    def __init__(self, name, body):
        self.name = name
        self.body = body


class Block(IRNode):
    def __init__(self, stmts):
        self.stmts = stmts


class VarDecl(IRNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Assign(IRNode):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr


class BinOp(IRNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class UnaryOp(IRNode):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr


class RelOp(IRNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class LogicalAnd(IRNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class LogicalOr(IRNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class LogicalNot(IRNode):
    def __init__(self, expr):
        self.expr = expr


class Identifier(IRNode):
    def __init__(self, name):
        self.name = name


class ArrayAccess(IRNode):
    def __init__(self, name, index):
        self.name = name
        self.index = index


class Constant(IRNode):
    def __init__(self, val):
        self.val = str(val)


class Return(IRNode):
    def __init__(self, expr):
        self.expr = expr


class Break(IRNode):
    pass


class Continue(IRNode):
    pass


class If(IRNode):
    def __init__(self, cond, true_block, false_block=None):
        self.cond = cond
        self.true_block = true_block
        self.false_block = false_block


class While(IRNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body


class DoWhile(IRNode):
    def __init__(self, body, cond):
        self.body = body
        self.cond = cond


class For(IRNode):
    def __init__(self, init, cond, step, body):
        self.init = init
        self.cond = cond
        self.step = step
        self.body = body


class FuncCall(IRNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args


class QuadGenerator:
    def __init__(self):
        self.quads = []
        self.next_quad = 0
        self.temp_count = 1
        self.loops = []

    def emit(self, op, arg1, arg2, result):
        self.quads.append([op, arg1, arg2, result])
        self.next_quad += 1
        return self.next_quad - 1

    def new_temp(self):
        temp = f"t{self.temp_count}"
        self.temp_count += 1
        return temp

    def backpatch(self, idx_list, target_quad):
        for idx in idx_list:
            self.quads[idx][3] = target_quad

    def gen_cond(self, node):
        if isinstance(node, RelOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            true_jump = self.emit(f"J{node.op}", left, right, "_")
            false_jump = self.emit("J", "_", "_", "_")
            return [true_jump], [false_jump]

        if isinstance(node, LogicalAnd):
            true_1, false_1 = self.gen_cond(node.left)
            self.backpatch(true_1, self.next_quad)
            true_2, false_2 = self.gen_cond(node.right)
            return true_2, false_1 + false_2

        if isinstance(node, LogicalOr):
            true_1, false_1 = self.gen_cond(node.left)
            self.backpatch(false_1, self.next_quad)
            true_2, false_2 = self.gen_cond(node.right)
            return true_1 + true_2, false_2

        if isinstance(node, LogicalNot):
            true_list, false_list = self.gen_cond(node.expr)
            return false_list, true_list

        result = self.visit(node)
        true_jump = self.emit("J!=", result, "0", "_")
        false_jump = self.emit("J", "_", "_", "_")
        return [true_jump], [false_jump]

    def generate(self, node):
        self.visit(node)

    def visit(self, node):
        if node is None:
            return None

        if isinstance(node, Program):
            for item in node.nodes:
                self.visit(item)

        elif isinstance(node, FuncDef):
            self.emit(node.name, "_", "_", "_")
            self.visit(node.body)
            if node.name == "main":
                self.emit("sys", "_", "_", "_")
            else:
                self.emit("ret", "_", "_", "_")

        elif isinstance(node, Block):
            for stmt in node.stmts:
                self.visit(stmt)

        elif isinstance(node, VarDecl):
            if node.value is not None:
                value = self.visit(node.value)
                self.emit("=", value, "_", node.name)

        elif isinstance(node, Assign):
            value = self.visit(node.expr)
            if isinstance(node.var, ArrayAccess):
                index = self.visit(node.var.index)
                self.emit("[]=", value, index, node.var.name)
                return node.var.name
            self.emit("=", value, "_", node.var)
            return node.var

        elif isinstance(node, BinOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            result = self.new_temp()
            self.emit(node.op, left, right, result)
            return result

        elif isinstance(node, UnaryOp):
            value = self.visit(node.expr)
            result = self.new_temp()
            self.emit(node.op, value, "_", result)
            return result

        elif isinstance(node, (RelOp, LogicalAnd, LogicalOr)):
            left = self.visit(node.left)
            right = self.visit(node.right)
            result = self.new_temp()
            op = node.op if isinstance(node, RelOp) else ("&&" if isinstance(node, LogicalAnd) else "||")
            self.emit(op, left, right, result)
            return result

        elif isinstance(node, LogicalNot):
            value = self.visit(node.expr)
            result = self.new_temp()
            self.emit("!", value, "_", result)
            return result

        elif isinstance(node, Identifier):
            return node.name

        elif isinstance(node, ArrayAccess):
            index = self.visit(node.index)
            result = self.new_temp()
            self.emit("=[]", node.name, index, result)
            return result

        elif isinstance(node, Constant):
            return node.val

        elif isinstance(node, FuncCall):
            if node.name == "read" and len(node.args) == 1 and isinstance(node.args[0], Identifier):
                result = self.new_temp()
                self.emit("call", node.name, "_", result)
                self.emit("=", result, "_", node.args[0].name)
                return result
            for arg in node.args:
                arg_value = self.visit(arg)
                self.emit("para", arg_value, "_", "_")
            result = self.new_temp()
            self.emit("call", node.name, "_", result)
            return result

        elif isinstance(node, Return):
            if node.expr is not None:
                value = self.visit(node.expr)
                self.emit("ret", "_", "_", value)
            else:
                self.emit("ret", "_", "_", "_")

        elif isinstance(node, Break):
            idx = self.emit("J", "_", "_", "_")
            if self.loops:
                self.loops[-1]["break"].append(idx)

        elif isinstance(node, Continue):
            idx = self.emit("J", "_", "_", "_")
            if self.loops:
                self.loops[-1]["continue"].append(idx)

        elif isinstance(node, If):
            true_list, false_list = self.gen_cond(node.cond)
            self.backpatch(true_list, self.next_quad)
            self.visit(node.true_block)
            if node.false_block:
                out_list = [self.emit("J", "_", "_", "_")]
                self.backpatch(false_list, self.next_quad)
                self.visit(node.false_block)
                self.backpatch(out_list, self.next_quad)
            else:
                self.backpatch(false_list, self.next_quad)

        elif isinstance(node, While):
            self.loops.append({"break": [], "continue": []})
            start_idx = self.next_quad
            true_list, false_list = self.gen_cond(node.cond)
            self.backpatch(true_list, self.next_quad)
            self.visit(node.body)
            self.emit("J", "_", "_", start_idx)
            exit_idx = self.next_quad
            self.backpatch(false_list, exit_idx)
            loop_info = self.loops.pop()
            self.backpatch(loop_info["break"], exit_idx)
            self.backpatch(loop_info["continue"], start_idx)

        elif isinstance(node, DoWhile):
            self.loops.append({"break": [], "continue": []})
            start_idx = self.next_quad
            self.visit(node.body)
            continue_idx = self.next_quad
            true_list, false_list = self.gen_cond(node.cond)
            self.backpatch(true_list, start_idx)
            exit_idx = self.next_quad
            self.backpatch(false_list, exit_idx)
            loop_info = self.loops.pop()
            self.backpatch(loop_info["break"], exit_idx)
            self.backpatch(loop_info["continue"], continue_idx)

        elif isinstance(node, For):
            self.loops.append({"break": [], "continue": []})
            if node.init:
                self.visit(node.init)
            cond_idx = self.next_quad
            if node.cond:
                true_list, false_list = self.gen_cond(node.cond)
            else:
                true_jump = self.emit("J", "_", "_", "_")
                true_list, false_list = [true_jump], []

            step_idx = self.next_quad
            if node.step:
                self.visit(node.step)
            self.emit("J", "_", "_", cond_idx)

            body_idx = self.next_quad
            self.backpatch(true_list, body_idx)
            self.visit(node.body)
            self.emit("J", "_", "_", step_idx)

            exit_idx = self.next_quad
            self.backpatch(false_list, exit_idx)
            loop_info = self.loops.pop()
            self.backpatch(loop_info["break"], exit_idx)
            self.backpatch(loop_info["continue"], step_idx)


def convert_ast(node: Optional[SharedASTNode]):
    if node is None:
        return None

    if node.name == "Empty":
        return None

    if node.name == "Program":
        return Program([converted for child in node.children if (converted := convert_ast(child)) is not None])

    if node.name == "FunctionDef":
        body = next((convert_ast(child) for child in node.children if child.name == "Compound"), Block([]))
        return FuncDef(_decl_name(node.value), body)

    if node.name == "Compound":
        return Block(_convert_statements(node.children))

    if node.name in {"VarDecl", "ConstDecl"}:
        init = convert_ast(node.children[0]) if node.children else None
        return VarDecl(_decl_name(node.value), init)

    if node.name == "ExprStmt":
        if not node.children:
            return None
        if len(node.children) == 1:
            return convert_ast(node.children[0])
        return Block(_convert_statements(node.children))

    if node.name == "=":
        var_name = convert_ast(node.children[0]) if node.children and node.children[0].name == "ArrayAccess" else (_assignment_target(node.children[0]) if node.children else "")
        expr = convert_ast(node.children[1]) if len(node.children) > 1 else None
        return Assign(var_name, expr)

    if node.name == "ArrayAccess":
        index = convert_ast(node.children[0]) if node.children else Constant(0)
        return ArrayAccess(node.value, index)

    if node.name in {"+", "-", "*", "/", "%"}:
        if node.name == "-" and len(node.children) == 1:
            return UnaryOp("-", convert_ast(node.children[0]))
        left = convert_ast(node.children[0]) if node.children else None
        right = convert_ast(node.children[1]) if len(node.children) > 1 else None
        return BinOp(node.name, left, right)

    if node.name in {">", "<", ">=", "<=", "==", "!="}:
        left = convert_ast(node.children[0]) if node.children else None
        right = convert_ast(node.children[1]) if len(node.children) > 1 else None
        return RelOp(node.name, left, right)

    if node.name == "&&":
        if len(node.children) < 2:
            return convert_ast(node.children[0]) if node.children else None
        return LogicalAnd(convert_ast(node.children[0]), convert_ast(node.children[1]))

    if node.name == "||":
        if len(node.children) < 2:
            return convert_ast(node.children[0]) if node.children else None
        return LogicalOr(convert_ast(node.children[0]), convert_ast(node.children[1]))

    if node.name == "!":
        return LogicalNot(convert_ast(node.children[0]) if node.children else None)

    if node.name == "Call":
        return FuncCall(node.value, [convert_ast(child) for child in node.children])

    if node.name == "ReturnStmt":
        return Return(convert_ast(node.children[0]) if node.children else None)

    if node.name == "BreakStmt":
        return Break()

    if node.name == "ContinueStmt":
        return Continue()

    if node.name == "IfStmt":
        cond = convert_ast(node.children[0]) if node.children else None
        true_block = _body_from_children(node.children[1:2])
        false_block = _body_from_children(node.children[2:]) if len(node.children) > 2 else None
        return If(cond, true_block, false_block)

    if node.name == "WhileStmt":
        cond = convert_ast(node.children[0]) if node.children else None
        return While(cond, _body_from_children(node.children[1:]))

    if node.name == "DoWhileStmt":
        if not node.children:
            return DoWhile(Block([]), None)
        return DoWhile(_body_from_children(node.children[:-1]), convert_ast(node.children[-1]))

    if node.name == "ForStmt":
        children = list(node.children)
        init = convert_ast(children[0]) if len(children) > 0 else None
        cond = convert_ast(children[1]) if len(children) > 1 else None
        step = convert_ast(children[2]) if len(children) > 2 else None
        body = _body_from_children(children[3:])
        return For(init, cond, step, body)

    if not node.children:
        text = node.value if node.value is not None else node.name
        if _is_literal(text):
            return Constant(_literal_value(text))
        return Identifier(text)

    return Block(_convert_statements(node.children))


def generate_quads(ast: Optional[SharedASTNode]) -> List[Tuple[object, object, object, object]]:
    ir_root = convert_ast(ast)
    generator = QuadGenerator()
    generator.generate(ir_root)
    return [tuple(quad) for quad in generator.quads]


def format_quads(quads) -> str:
    lines = []
    for index, quad in enumerate(quads):
        parts = []
        for item in quad:
            if isinstance(item, int):
                parts.append(str(item))
            elif item == "_":
                parts.append("'_'")
            else:
                parts.append(f"'{str(item).strip()}'")
        lines.append(f"{index}: ({parts[0]}, {parts[1]}, {parts[2]}, {parts[3]})")
    return "\n".join(lines) + ("\n" if lines else "")


def _convert_statements(children):
    return [converted for child in children if (converted := convert_ast(child)) is not None]


def _body_from_children(children):
    converted = _convert_statements(children)
    if len(converted) == 1:
        return converted[0]
    return Block(converted)


def _decl_name(value):
    parts = value.split() if value else []
    return re.sub(r"\[.*\]$", "", parts[-1].replace(",", "")) if parts else ""


def _assignment_target(node):
    if node.value is not None:
        return node.value
    return node.name


def _is_literal(text):
    return bool(re.match(r"^\d+(?:\.\d+)?$", text) or re.match(r"^'.*'$", text) or re.match(r'^".*"$', text))


def _literal_value(text):
    if re.match(r"^'.*'$", text):
        return text[1:-1]
    if re.match(r'^".*"$', text):
        return text
    return text
