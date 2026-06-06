import re
from typing import Dict, List, Optional, Tuple

from .models import ASTNode, Diagnostic, SymbolInfo, max_line


ARITHMETIC_OPERATORS = {"+", "-", "*", "/", "%"}
RELATIONAL_OPERATORS = {">", "<", "==", "!=", ">=", "<="}
LOGICAL_OPERATORS = {"&&", "||"}
EXPRESSION_OPERATORS = ARITHMETIC_OPERATORS | RELATIONAL_OPERATORS | LOGICAL_OPERATORS
KEYWORDS = {
    "int",
    "float",
    "char",
    "void",
    "const",
    "return",
    "break",
    "continue",
    "if",
    "else",
    "while",
    "do",
    "for",
    "switch",
    "case",
    "default",
}

BUILTIN_FUNCTIONS = {
    "read": {"type": "int", "params": []},
    "write": {"type": "void", "params": ["any"]},
}


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table_stack: List[Dict[str, SymbolInfo]] = [{}]
        self.errors: List[Tuple[int, int]] = []
        self.diagnostics: List[Diagnostic] = []
        self.history_symbols: Dict[str, List[SymbolInfo]] = {"const": [], "var": [], "func": []}

        self.current_func_ret_type: Optional[str] = None
        self.current_func_has_return = False
        self.current_func_has_mismatch_return = False
        self.pending_function_calls: List[Tuple[int, str]] = []

    def analyze_program(self, node: ASTNode):
        self.analyze(node, in_loop=False)
        self.resolve_pending_function_calls()
        self.errors.sort(key=lambda item: (item[0], item[1]))
        self.diagnostics = [
            Diagnostic("semantic", line, str(code), self.message_for_code(code))
            for line, code in self.errors
        ]
        return self

    def message_for_code(self, code: int) -> str:
        return {
            301: "duplicate declaration",
            302: "undeclared identifier",
            303: "duplicate function declaration or definition",
            304: "undefined function",
            305: "argument count mismatch",
            306: "argument type mismatch",
            307: "return type mismatch or missing return",
            308: "illegal break or continue outside loop",
            309: "assignment to const",
            310: "expression type mismatch",
        }.get(code, "semantic error")

    def report_error(self, line: Optional[int], code: int) -> None:
        error = (line or 0, code)
        if error not in self.errors:
            self.errors.append(error)

    def enter_scope(self) -> None:
        self.symbol_table_stack.append({})

    def exit_scope(self) -> None:
        if len(self.symbol_table_stack) > 1:
            self.symbol_table_stack.pop()

    def declare_symbol(
        self,
        name: str,
        sym_type: str,
        kind: str,
        line: Optional[int],
        params: Optional[List[str]] = None,
        is_def: bool = False,
    ) -> None:
        current_scope = self.symbol_table_stack[-1]
        params = params or []
        existing = current_scope.get(name)

        if existing:
            if kind == "func" and existing.get("kind") == "func":
                same_signature = existing.get("type") == sym_type and existing.get("params", []) == params
                if not same_signature:
                    self.report_error(line, 303)
                elif existing.get("is_defined") and is_def:
                    self.report_error(line, 303)
                elif not is_def:
                    self.report_error(line, 303)
                else:
                    existing["is_defined"] = True
            else:
                self.report_error(line, 301)
            return

        current_scope[name] = {
            "name": name,
            "type": sym_type,
            "kind": kind,
            "params": params,
            "is_defined": is_def,
        }
        self.history_symbols[kind].append({"name": name, "type": sym_type, "params": params})

    def lookup_symbol(self, name: str) -> Optional[SymbolInfo]:
        for scope in reversed(self.symbol_table_stack):
            symbol = scope.get(name)
            if symbol:
                return symbol
        return None

    def analyze(self, node: Optional[ASTNode], in_loop: bool = False) -> None:
        if node is None:
            return

        if node.name == "Program":
            for child in node.children:
                self.analyze(child, in_loop)
            return

        if node.name in {"FunctionDecl", "FunctionDef"}:
            self.analyze_function(node)
            return

        if node.name == "Compound":
            self.enter_scope()
            for child in node.children:
                self.analyze(child, in_loop)
            self.exit_scope()
            return

        if node.name in {"VarDecl", "ConstDecl"}:
            self.analyze_declaration(node)
            return

        if node.name == "ReturnStmt":
            self.analyze_return(node)
            return

        if node.name in {"BreakStmt", "ContinueStmt"}:
            if not in_loop:
                self.report_error(node.line, 308)
            return

        if node.name == "ForStmt":
            self.enter_scope()
            children = list(node.children)
            if children:
                init = children[0]
                if init.name == "Empty":
                    pass
                elif init.name in {"VarDecl", "ConstDecl"}:
                    self.analyze_declaration(init)
                else:
                    self.evaluate_expression(init)
            if len(children) > 1 and children[1].name != "Empty":
                self.evaluate_expression(children[1])
            if len(children) > 2 and children[2].name != "Empty":
                self.evaluate_expression(children[2])
            for child in children[3:]:
                self.analyze(child, in_loop=True)
            self.exit_scope()
            return

        if node.name == "WhileStmt":
            if node.children:
                self.evaluate_expression(node.children[0])
            for child in node.children[1:]:
                self.analyze(child, in_loop=True)
            return

        if node.name == "DoWhileStmt":
            if node.children:
                for child in node.children[:-1]:
                    self.analyze(child, in_loop=True)
                self.evaluate_expression(node.children[-1])
            return

        if node.name == "IfStmt":
            if node.children:
                self.evaluate_expression(node.children[0])
            for child in node.children[1:]:
                self.analyze(child, in_loop)
            return

        if node.name == "ExprStmt":
            for child in node.children:
                self.evaluate_expression(child)
            return

        if node.name == "=":
            self.evaluate_assignment(node)
            return

        if node.name == "Call" or node.name in EXPRESSION_OPERATORS:
            self.evaluate_expression(node)
            return

        for child in node.children:
            self.analyze(child, in_loop)

    def analyze_function(self, node: ASTNode) -> None:
        ret_type, func_name = self.split_decl_value(node.value)
        params: List[str] = []
        param_symbols: List[Tuple[str, str, Optional[int]]] = []

        for child in node.children:
            if child.name == "Param":
                param_type, param_name = self.split_decl_value(child.value)
                params.append(param_type)
                if param_name:
                    param_symbols.append((param_name, param_type, child.line))

        is_definition = node.name == "FunctionDef" or any(child.name == "Compound" for child in node.children)
        self.declare_symbol(func_name, ret_type, "func", node.line, params, is_def=is_definition)

        if not is_definition:
            return

        saved_ret_type = self.current_func_ret_type
        saved_has_return = self.current_func_has_return
        saved_has_mismatch = self.current_func_has_mismatch_return

        self.current_func_ret_type = ret_type
        self.current_func_has_return = False
        self.current_func_has_mismatch_return = False

        self.enter_scope()
        for param_name, param_type, param_line in param_symbols:
            self.declare_symbol(param_name, param_type, "var", param_line)

        for child in node.children:
            if child.name == "Compound":
                for stmt in child.children:
                    self.analyze(stmt, in_loop=False)
            elif child.name != "Param":
                self.analyze(child, in_loop=False)

        end_line = max_line(node)
        if self.current_func_ret_type != "void":
            allow_implicit_main_return = func_name == "main" and not self.current_func_has_return
            if (not self.current_func_has_return and not allow_implicit_main_return) or self.current_func_has_mismatch_return:
                self.report_error(end_line, 307)
        elif self.current_func_has_mismatch_return:
            self.report_error(end_line, 307)

        self.exit_scope()
        self.current_func_ret_type = saved_ret_type
        self.current_func_has_return = saved_has_return
        self.current_func_has_mismatch_return = saved_has_mismatch

    def analyze_declaration(self, node: ASTNode) -> None:
        var_type, var_name = self.split_decl_value(node.value)
        if not var_name:
            return

        kind = "const" if node.name == "ConstDecl" else "var"
        self.declare_symbol(var_name, var_type, kind, node.line)

        if node.children:
            init_type = self.evaluate_expression(node.children[0])
            if init_type != "unknown" and var_type != "unknown" and init_type != var_type:
                self.report_error(node.children[0].line or node.line, 310)

    def analyze_return(self, node: ASTNode) -> None:
        self.current_func_has_return = True
        if not node.children:
            if self.current_func_ret_type != "void":
                self.current_func_has_mismatch_return = True
            return

        ret_type = self.evaluate_expression(node.children[0])
        if self.current_func_ret_type == "void":
            return
        elif ret_type != "unknown" and ret_type != self.current_func_ret_type:
            self.current_func_has_mismatch_return = True

    def evaluate_expression(self, node: Optional[ASTNode]) -> str:
        if node is None:
            return "unknown"

        if node.name == "=":
            return self.evaluate_assignment(node)

        if node.name == "!" and len(node.children) == 1:
            self.evaluate_expression(node.children[0])
            return "int"

        if node.name == "-" and len(node.children) == 1:
            return self.evaluate_expression(node.children[0])

        if node.name in ARITHMETIC_OPERATORS:
            return self.evaluate_binary_expression(node, require_same_type=True)

        if node.name in RELATIONAL_OPERATORS or node.name in LOGICAL_OPERATORS:
            self.evaluate_binary_expression(node, require_same_type=True)
            return "int"

        if node.name == "Call":
            return self.evaluate_call(node)

        if node.name == "ArrayAccess":
            return self.evaluate_array_access(node)

        if not node.children:
            return self.evaluate_leaf(node)

        result_type = "unknown"
        for child in node.children:
            result_type = self.evaluate_expression(child)
        return result_type

    def evaluate_assignment(self, node: ASTNode) -> str:
        if not node.children:
            return "unknown"

        target = node.children[0]
        var_name = self.array_base_name(target) if target.name == "ArrayAccess" else self.node_text(target).replace(",", "")
        symbol = self.lookup_symbol(var_name)
        left_type = "unknown"

        if not symbol:
            self.report_error(target.line or node.line, 302)
        else:
            left_type = symbol.get("type", "unknown")
            if symbol.get("kind") == "const":
                self.report_error(node.line, 309)

        right_type = "unknown"
        if len(node.children) > 1:
            right_type = self.evaluate_expression(node.children[1])

        if left_type != "unknown" and right_type != "unknown" and left_type != right_type:
            self.report_error(node.line, 310)
            return "unknown"
        return left_type

    def evaluate_array_access(self, node: ASTNode) -> str:
        array_name = self.node_text(node).replace(",", "")
        symbol = self.lookup_symbol(array_name)
        if not symbol:
            self.report_error(node.line, 302)
            return "unknown"
        if node.children:
            index_type = self.evaluate_expression(node.children[0])
            if index_type != "unknown" and index_type != "int":
                self.report_error(node.line, 310)
        return symbol.get("type", "unknown")

    def evaluate_binary_expression(self, node: ASTNode, require_same_type: bool) -> str:
        if len(node.children) < 2:
            return "unknown"

        left_type = self.evaluate_expression(node.children[0])
        right_type = self.evaluate_expression(node.children[1])
        if require_same_type and left_type != "unknown" and right_type != "unknown" and left_type != right_type:
            self.report_error(node.line, 310)
            return "unknown"
        return left_type

    def evaluate_call(self, node: ASTNode) -> str:
        func_name = node.value or self.node_text(node)
        symbol = self.lookup_symbol(func_name)
        actual_params = node.children
        builtin = BUILTIN_FUNCTIONS.get(func_name)

        if func_name == "read" and builtin is not None and len(actual_params) <= 1:
            for param in actual_params:
                self.evaluate_expression(param)
            return "int"

        if not symbol or symbol.get("kind") != "func":
            if builtin is None:
                self.report_error(node.line, 304)
                for param in actual_params:
                    self.evaluate_expression(param)
                return "unknown"
            symbol = {"name": func_name, "kind": "func", "type": builtin["type"], "params": builtin["params"], "is_defined": True}

        if not symbol.get("is_defined") and builtin is None:
            self.pending_function_calls.append((node.line or 0, func_name))

        expected_params = symbol.get("params", [])
        if len(expected_params) != len(actual_params):
            self.report_error(node.line, 305)
            for param in actual_params:
                self.evaluate_expression(param)
            return symbol.get("type", "unknown")

        for index, param in enumerate(actual_params):
            param_type = self.evaluate_expression(param)
            if expected_params[index] != "any" and param_type != "unknown" and param_type != expected_params[index]:
                self.report_error(node.line, 306)
        return symbol.get("type", "unknown")

    def resolve_pending_function_calls(self) -> None:
        for line, func_name in self.pending_function_calls:
            if func_name in BUILTIN_FUNCTIONS:
                continue
            symbol = self.lookup_symbol(func_name)
            if not symbol or symbol.get("kind") != "func" or not symbol.get("is_defined"):
                self.report_error(line, 304)

    def evaluate_leaf(self, node: ASTNode) -> str:
        text = self.node_text(node).replace(",", "")
        symbol = self.lookup_symbol(text)
        if symbol:
            return symbol.get("type", "unknown")

        literal_type = self.infer_literal_type(text)
        if literal_type != "unknown":
            return literal_type

        if re.match(r"^[A-Za-z_]\w*$", text) and text not in KEYWORDS:
            self.report_error(node.line, 302)
        return "unknown"

    def infer_literal_type(self, text: str) -> str:
        if re.match(r"^-?\d+$", text):
            return "int"
        if re.match(r"^-?\d+\.\d+$", text):
            return "float"
        if re.match(r"^'.*'$", text):
            return "char"
        if re.match(r'^".*"$', text):
            return "string"
        return "unknown"

    def split_decl_value(self, value: Optional[str]) -> Tuple[str, str]:
        parts = value.split() if value else []
        if len(parts) >= 2:
            return parts[0], re.sub(r"\[.*\]$", "", parts[1].replace(",", ""))
        if len(parts) == 1:
            return parts[0], ""
        return "unknown", "unknown"

    def node_text(self, node: ASTNode) -> str:
        return node.value if node.value is not None else node.name

    def array_base_name(self, node: ASTNode) -> str:
        return self.node_text(node).replace(",", "")
