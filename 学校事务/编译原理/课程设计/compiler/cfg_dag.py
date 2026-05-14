from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple


Quad = Tuple[object, object, object, object]
ARITHMETIC_OPS = {"+", "-", "*", "/", "%"}
TERMINAL_OPS = {"ret", "return", "sys"}


@dataclass
class BasicBlock:
    name: str
    start: int
    end: int
    quads: List[Quad]
    leader_reasons: List[str] = field(default_factory=list)


@dataclass
class ControlFlowGraph:
    successors: Dict[str, List[str]]
    predecessors: Dict[str, List[str]]


@dataclass
class CommonSubexpression:
    block: str
    expression: str
    original: str
    reused_by: List[str] = field(default_factory=list)


@dataclass
class DagNode:
    id: str
    label: str
    children: List[str] = field(default_factory=list)
    names: List[str] = field(default_factory=list)


@dataclass
class DagBlock:
    block: str
    nodes: List[DagNode]
    optimized_quads: List[Quad]


@dataclass
class ControlFlowAnalysis:
    basic_blocks: List[BasicBlock]
    cfg: ControlFlowGraph
    dag_blocks: List[DagBlock]
    common_subexpressions: List[CommonSubexpression]
    optimized_quads: List[Quad]
    basic_blocks_text: str
    cfg_text: str
    dag_text: str
    dag_optimized_quads_text: str


def analyze_control_flow(quads: Iterable[Quad]) -> ControlFlowAnalysis:
    quad_list = [tuple(quad) for quad in quads]
    blocks = build_basic_blocks(quad_list)
    cfg = build_cfg(blocks)
    dag_blocks, common_subexpressions, optimized_quads = optimize_blocks_with_dag(blocks)
    return ControlFlowAnalysis(
        basic_blocks=blocks,
        cfg=cfg,
        dag_blocks=dag_blocks,
        common_subexpressions=common_subexpressions,
        optimized_quads=optimized_quads,
        basic_blocks_text=format_basic_blocks(blocks),
        cfg_text=format_cfg(cfg),
        dag_text=format_dags(dag_blocks, common_subexpressions),
        dag_optimized_quads_text=format_dag_optimized_quads(optimized_quads),
    )


def build_basic_blocks(quads: List[Quad]) -> List[BasicBlock]:
    if not quads:
        return []

    leader_reasons: Dict[int, List[str]] = {0: ["entry"]}
    for index, quad in enumerate(quads):
        op = str(quad[0])
        target = quad[3]
        if _is_function_label(quad):
            leader_reasons.setdefault(index, []).append(f"function entry {op}")
        if op.startswith("J"):
            if isinstance(target, int) and 0 <= target < len(quads):
                leader_reasons.setdefault(target, []).append(f"jump target from {index}")
            if index + 1 < len(quads):
                leader_reasons.setdefault(index + 1, []).append(f"fall-through after jump {index}")

    ordered = sorted(leader_reasons)
    blocks: List[BasicBlock] = []
    for block_index, start in enumerate(ordered):
        next_start = ordered[block_index + 1] if block_index + 1 < len(ordered) else len(quads)
        end = next_start - 1
        blocks.append(BasicBlock(f"B{block_index}", start, end, quads[start : end + 1], leader_reasons.get(start, [])))
    return blocks


def build_cfg(blocks: List[BasicBlock]) -> ControlFlowGraph:
    index_to_block = {index: block.name for block in blocks for index in range(block.start, block.end + 1)}
    successors = {block.name: [] for block in blocks}
    predecessors = {block.name: [] for block in blocks}

    for block_index, block in enumerate(blocks):
        if not block.quads:
            continue
        op, _arg1, _arg2, result = block.quads[-1]
        op_text = str(op)
        next_block = blocks[block_index + 1].name if block_index + 1 < len(blocks) else None

        if op_text == "J":
            _add_edge(block.name, index_to_block.get(result), successors, predecessors)
        elif op_text.startswith("J"):
            _add_edge(block.name, index_to_block.get(result), successors, predecessors)
            _add_edge(block.name, next_block, successors, predecessors)
        elif op_text not in TERMINAL_OPS:
            _add_edge(block.name, next_block, successors, predecessors)

    return ControlFlowGraph(successors=successors, predecessors=predecessors)


def optimize_blocks_with_dag(blocks: List[BasicBlock]) -> Tuple[List[DagBlock], List[CommonSubexpression], List[Quad]]:
    dag_blocks: List[DagBlock] = []
    common_subexpressions: List[CommonSubexpression] = []
    optimized_all: List[Quad] = []

    for block in blocks:
        optimizer = LocalDagOptimizer(block)
        dag_block = optimizer.optimize()
        dag_blocks.append(dag_block)
        common_subexpressions.extend(optimizer.common_subexpressions)
        optimized_all.extend(dag_block.optimized_quads)

    return dag_blocks, common_subexpressions, optimized_all


class LocalDagOptimizer:
    def __init__(self, block: BasicBlock):
        self.block = block
        self.nodes: List[DagNode] = []
        self.leaf_nodes: Dict[object, str] = {}
        self.expression_nodes: Dict[Tuple[object, object, object], str] = {}
        self.value_names: Dict[object, str] = {}
        self.common_subexpressions: List[CommonSubexpression] = []
        self.optimized_quads: List[Quad] = []

    def optimize(self) -> DagBlock:
        for quad in self.block.quads:
            op, arg1, arg2, result = quad
            if op in ARITHMETIC_OPS:
                self._handle_arithmetic(str(op), arg1, arg2, result)
            elif op == "=":
                value = self._resolve(arg1)
                self.optimized_quads.append(("=", value, "_", result))
                self.value_names[result] = value
                self._attach_name(value, str(result))
            else:
                self.optimized_quads.append(quad)
        return DagBlock(self.block.name, self.nodes, self.optimized_quads)

    def _handle_arithmetic(self, op: str, arg1, arg2, result) -> None:
        left = self._resolve(arg1)
        right = self._resolve(arg2)
        key = self._expression_key(op, left, right)
        expression = f"{left} {op} {right}"

        if key in self.expression_nodes:
            node_id = self.expression_nodes[key]
            original = self._primary_name(node_id)
            self.optimized_quads.append(("=", original, "_", result))
            self.value_names[result] = original
            self._attach_name(node_id, str(result))
            self.common_subexpressions.append(CommonSubexpression(self.block.name, expression, original, [str(result)]))
            return

        left_id = self._leaf(left)
        right_id = self._leaf(right)
        node_id = self._node(f"{op}", [left_id, right_id], [str(result)])
        self.expression_nodes[key] = node_id
        self.value_names[result] = result
        self.optimized_quads.append((op, left, right, result))

    def _leaf(self, value) -> str:
        if value in self.leaf_nodes:
            return self.leaf_nodes[value]
        node_id = self._node(str(value), [], [str(value)])
        self.leaf_nodes[value] = node_id
        return node_id

    def _node(self, label: str, children: List[str], names: List[str]) -> str:
        node_id = f"N{len(self.nodes)}"
        self.nodes.append(DagNode(node_id, label, children, names))
        return node_id

    def _resolve(self, value):
        while value in self.value_names and self.value_names[value] != value:
            value = self.value_names[value]
        return value

    def _expression_key(self, op: str, left, right) -> Tuple[object, object, object]:
        if op in {"+", "*"}:
            ordered = tuple(sorted((str(left), str(right))))
            return op, ordered[0], ordered[1]
        return op, left, right

    def _primary_name(self, node_id: str) -> str:
        for node in self.nodes:
            if node.id == node_id and node.names:
                return node.names[0]
        return node_id

    def _attach_name(self, value, name: str) -> None:
        node_id = self.expression_nodes.get(value) or self.leaf_nodes.get(value)
        if node_id is None and isinstance(value, str):
            node_id = next((node.id for node in self.nodes if value in node.names), None)
        if node_id is None:
            return
        for node in self.nodes:
            if node.id == node_id and name not in node.names:
                node.names.append(name)
                return


def format_basic_blocks(blocks: List[BasicBlock]) -> str:
    if not blocks:
        return "Basic Blocks\n\n(no quadruples)\n"
    lines = ["Basic Blocks", "", "Leaders", "Index | Block | Reason", "--- | --- | ---"]
    for block in blocks:
        lines.append(f"{block.start} | {block.name} | {'; '.join(block.leader_reasons) or '-'}")
    lines.extend(["", "Blocks"])
    for block in blocks:
        lines.append(f"{block.name} [{block.start}..{block.end}]")
        for offset, quad in enumerate(block.quads, block.start):
            lines.append(f"  {offset}: {_format_quad(quad)}")
    return "\n".join(lines) + "\n"


def format_cfg(cfg: ControlFlowGraph) -> str:
    lines = ["Control Flow Graph", "Block | Successors | Predecessors", "--- | --- | ---"]
    for block, edges in cfg.successors.items():
        target_text = ", ".join(edges) if edges else "-"
        pred_text = ", ".join(cfg.predecessors.get(block, [])) or "-"
        lines.append(f"{block} | {target_text} | {pred_text}")
    return "\n".join(lines) + "\n"


def format_dags(dag_blocks: List[DagBlock], common_subexpressions: List[CommonSubexpression]) -> str:
    lines = ["DAG"]
    for dag in dag_blocks:
        lines.append(dag.block)
        for node in dag.nodes:
            names = f" {{{', '.join(node.names)}}}" if node.names else ""
            children = f" <- {', '.join(node.children)}" if node.children else ""
            lines.append(f"  {node.id}: {node.label}{names}{children}")
        for record in common_subexpressions:
            if record.block == dag.block:
                lines.append(f"  common: {record.expression} reused by {', '.join(record.reused_by)}")
    return "\n".join(lines) + "\n"


def format_dag_optimized_quads(quads: List[Quad]) -> str:
    lines = ["DAG optimized quadruples", f"Optimized instruction count: {len(quads)}", ""]
    lines.extend(f"{index}: {_format_quad(quad)}" for index, quad in enumerate(quads))
    return "\n".join(lines) + "\n"


def _add_edge(source: str, target: str | None, successors: Dict[str, List[str]], predecessors: Dict[str, List[str]]) -> None:
    if target is None:
        return
    if target not in successors[source]:
        successors[source].append(target)
    if source not in predecessors[target]:
        predecessors[target].append(source)


def _is_function_label(quad: Quad) -> bool:
    op, arg1, arg2, result = quad
    return (
        isinstance(op, str)
        and arg1 == "_"
        and arg2 == "_"
        and result == "_"
        and op not in {"J", "sys", "ret", "return"}
    )


def _format_quad(quad: Quad) -> str:
    op, arg1, arg2, result = quad
    return f"({op}, {arg1}, {arg2}, {result})"
