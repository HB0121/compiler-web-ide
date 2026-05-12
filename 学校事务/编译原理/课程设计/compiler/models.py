from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Token:
    text: str
    code: int
    line: int
    column: int = 1
    kind: str = ""


@dataclass
class Diagnostic:
    phase: str
    line: int
    code: str
    message: str

    def format(self) -> str:
        return f"{self.line} {self.code} {self.phase}: {self.message}"


@dataclass
class ASTNode:
    name: str
    line: Optional[int] = None
    value: Optional[str] = None
    children: List["ASTNode"] = field(default_factory=list)

    def add_child(self, child: Optional["ASTNode"]) -> None:
        if child is not None:
            self.children.append(child)


@dataclass
class PipelineResult:
    tokens: List[Token]
    ast: Optional[ASTNode]
    diagnostics: List[Diagnostic]
    const_symbols: List[Dict[str, object]]
    var_symbols: List[Dict[str, object]]
    function_symbols: List[Dict[str, object]]
    quads: List[Tuple[object, object, object, object]]
    texts: Dict[str, str]


def format_ast(node: Optional[ASTNode], level: int = 0) -> str:
    if node is None:
        return ""
    lines: List[str] = []

    def walk(current: ASTNode, depth: int) -> None:
        indent = "  " * depth
        if current.name in {"Program", "Compound", "IfStmt", "WhileStmt", "ForStmt", "DoWhileStmt", "ExprStmt"}:
            label = current.name
        elif current.name in {"VarDecl", "ConstDecl", "FunctionDecl", "FunctionDef", "Param"}:
            label = f"{current.name}({current.value})[{current.line}]"
        elif current.name == "Call":
            label = f"Call({current.value})[{current.line}]"
        elif current.name in {"ContinueStmt", "BreakStmt", "ReturnStmt"}:
            label = f"{current.name}[{current.line}]"
        elif current.children or current.line is None:
            label = current.value if current.value else current.name
        else:
            label = f"{current.value or current.name}[{current.line}]"
        lines.append(f"{indent}{label}")
        for child in current.children:
            walk(child, depth + 1)

    walk(node, level)
    return "\n".join(lines) + "\n"


def max_line(node: Optional[ASTNode]) -> int:
    if node is None:
        return 0
    current = node.line or 0
    for child in node.children:
        current = max(current, max_line(child))
    return current
