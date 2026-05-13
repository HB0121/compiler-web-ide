package com.huangbin.compiler.ir;

import java.util.*;

/**
 * DAG 优化器 + 控制流图分析
 * - 基本块划分
 * - 基于 DAG 的局部公共子表达式消除
 * - 控制流图构建与文本输出
 *
 * @author 黄彬 (12303070250)
 */
public class DAGOptimizer {

    private final List<IRGenerator.Quad> quads;

    public DAGOptimizer(List<IRGenerator.Quad> quads) {
        this.quads = quads;
    }

    // ==================== 基本块 ====================

    public static class BasicBlock {
        public final int id;
        public final int startIdx;        // 起始四元式索引 (inclusive)
        public final int endIdx;          // 结束四元式索引 (inclusive)
        public final List<IRGenerator.Quad> quads = new ArrayList<>();
        public final Set<Integer> successors = new LinkedHashSet<>();
        public final Set<Integer> predecessors = new LinkedHashSet<>();
        public final List<String> dagLog = new ArrayList<>();   // DAG 优化日志

        BasicBlock(int id, int startIdx, int endIdx) {
            this.id = id; this.startIdx = startIdx; this.endIdx = endIdx;
        }

        public boolean isEmpty() { return quads.isEmpty(); }

        @Override
        public String toString() {
            return String.format("B%d [%d..%d] preds=%s succs=%s", id, startIdx, endIdx, predecessors, successors);
        }
    }

    // ==================== DAG 节点 ====================

    static class DAGNode {
        final String op, arg1, arg2;
        final int id;
        String label;          // 该节点对应的变量名（如果有）
        final Set<String> labels = new LinkedHashSet<>(); // 所有关联变量名
        final Set<DAGNode> children = new LinkedHashSet<>();

        DAGNode(int id, String op, String arg1, String arg2) {
            this.id = id; this.op = op; this.arg1 = arg1; this.arg2 = arg2; this.label = "";
        }

        String key() { return op + "|" + arg1 + "|" + arg2; }

        @Override
        public String toString() { return "n" + id + ":" + op + (labels.isEmpty() ? "" : " " + labels); }
    }

    // ==================== 主入口 ====================

    /**
     * 划分基本块，对每个块做 DAG 优化，构建控制流图
     */
    public OptimizationResult optimize() {
        List<BasicBlock> blocks = splitBasicBlocks();
        int totalEliminated = 0;

        // 识别领导人
        Set<Integer> leaders = new LinkedHashSet<>();
        leaders.add(0);
        for (int i = 0; i < quads.size(); i++) {
            IRGenerator.Quad q = quads.get(i);
            if (q.op.equals("FUNC")) leaders.add(i);
            if (q.op.equals("J") || q.op.equals("J!=")) {
                try { leaders.add(Integer.parseInt(q.result)); } catch (NumberFormatException ignored) {}
                if (i + 1 < quads.size()) leaders.add(i + 1);
            }
            if (q.op.equals("RET")) {
                if (i + 1 < quads.size()) leaders.add(i + 1);
            }
            if (q.op.equals("CALL") && q.arg1.equals("main") && i + 1 < quads.size()) {
                leaders.add(i + 1);
            }
            if (q.op.equals("EXIT") && i + 1 < quads.size()) {
                leaders.add(i + 1);
            }
        }

        // 按领导人索引重新划分
        blocks.clear();
        List<Integer> sortedLeaders = new ArrayList<>(leaders);
        Collections.sort(sortedLeaders);

        for (int li = 0; li < sortedLeaders.size(); li++) {
            int start = sortedLeaders.get(li);
            int end = (li + 1 < sortedLeaders.size()) ? sortedLeaders.get(li + 1) - 1 : quads.size() - 1;
            BasicBlock bb = new BasicBlock(li, start, end);
            for (int j = start; j <= end; j++) {
                IRGenerator.Quad q = quads.get(j);
                bb.quads.add(q);
            }
            blocks.add(bb);
        }

        // 构建控制流边
        buildCFGEdges(blocks);

        // 对每个基本块做 DAG 局部优化
        for (BasicBlock bb : blocks) {
            int eliminated = optimizeBlock(bb);
            totalEliminated += eliminated;
        }

        // 生成结果
        String flowGraph = buildFlowGraphText(blocks);
        String dagSummary = buildDAGSummary(blocks);
        List<IRGenerator.Quad> optimizedQuads = rebuildQuads(blocks);

        return new OptimizationResult(blocks, flowGraph, dagSummary, optimizedQuads, totalEliminated);
    }

    // ==================== 基本块划分 ====================

    private List<BasicBlock> splitBasicBlocks() {
        // 先收集所有可作为跳转目标的四元式索引
        Set<Integer> jumpTargets = new LinkedHashSet<>();
        for (int i = 0; i < quads.size(); i++) {
            IRGenerator.Quad q = quads.get(i);
            if (q.op.equals("J") || q.op.equals("J!=")) {
                try { jumpTargets.add(Integer.parseInt(q.result)); } catch (NumberFormatException ignored) {}
            }
        }

        List<BasicBlock> blocks = new ArrayList<>();
        int blockId = 0;
        int start = 0;
        for (int i = 0; i < quads.size(); i++) {
            IRGenerator.Quad q = quads.get(i);
            boolean isEnd = false;

            // 基本块结束条件：跳转指令、RET、CALL main、EXIT
            if (q.op.equals("J") || q.op.equals("J!=") || q.op.equals("RET") || q.op.equals("EXIT")) {
                isEnd = true;
            }
            // CALL main 后面通常是入口结束
            if (q.op.equals("CALL") && q.arg1.equals("main")) {
                isEnd = true;
            }

            // 下一个是跳转目标或 FUNC，当前指令结束当前块
            if (i + 1 < quads.size() && (jumpTargets.contains(i + 1) || quads.get(i + 1).op.equals("FUNC"))) {
                isEnd = true;
            }

            if (isEnd) {
                BasicBlock bb = new BasicBlock(blockId++, start, i);
                for (int j = start; j <= i; j++) bb.quads.add(quads.get(j));
                blocks.add(bb);
                start = i + 1;
            }
        }
        // 剩余部分
        if (start < quads.size()) {
            BasicBlock bb = new BasicBlock(blockId, start, quads.size() - 1);
            for (int j = start; j < quads.size(); j++) bb.quads.add(quads.get(j));
            blocks.add(bb);
        }
        return blocks;
    }

    // ==================== 控制流图边 ====================

    private void buildCFGEdges(List<BasicBlock> blocks) {
        Map<Integer, Integer> indexToBlock = new HashMap<>();
        for (BasicBlock bb : blocks) {
            indexToBlock.put(bb.startIdx, bb.id);
        }

        for (int bi = 0; bi < blocks.size(); bi++) {
            BasicBlock bb = blocks.get(bi);
            if (bb.quads.isEmpty()) continue;
            IRGenerator.Quad last = bb.quads.get(bb.quads.size() - 1);

            if (last.op.equals("J")) {
                // 无条件跳转
                try {
                    int target = Integer.parseInt(last.result);
                    Integer targetBlock = findBlockByIndex(blocks, target);
                    if (targetBlock != null) {
                        bb.successors.add(targetBlock);
                        blocks.get(targetBlock).predecessors.add(bb.id);
                    }
                } catch (NumberFormatException ignored) {}
            } else if (last.op.equals("J!=")) {
                // 条件跳转：两条边
                try {
                    int target = Integer.parseInt(last.result);
                    Integer targetBlock = findBlockByIndex(blocks, target);
                    if (targetBlock != null) {
                        bb.successors.add(targetBlock);
                        blocks.get(targetBlock).predecessors.add(bb.id);
                    }
                } catch (NumberFormatException ignored) {}
                // 顺序下一条
                if (bi + 1 < blocks.size()) {
                    bb.successors.add(bi + 1);
                    blocks.get(bi + 1).predecessors.add(bb.id);
                }
            } else if (last.op.equals("RET") || last.op.equals("EXIT")) {
                // 无后继
            } else {
                // 顺序下一条
                if (bi + 1 < blocks.size()) {
                    bb.successors.add(bi + 1);
                    blocks.get(bi + 1).predecessors.add(bb.id);
                }
            }
        }
    }

    private Integer findBlockByIndex(List<BasicBlock> blocks, int quadIdx) {
        for (BasicBlock bb : blocks) {
            if (bb.startIdx <= quadIdx && quadIdx <= bb.endIdx) return bb.id;
        }
        return null;
    }

    // ==================== DAG 局部优化 ====================

    private int optimizeBlock(BasicBlock bb) {
        List<DAGNode> dag = new ArrayList<>();
        Map<String, DAGNode> nodeMap = new HashMap<>();  // key → DAGNode
        Map<String, DAGNode> varMap = new HashMap<>();    // variable → DAGNode (最新定义)
        int nodeId = 0;
        int eliminated = 0;

        for (int qi = 0; qi < bb.quads.size(); qi++) {
            IRGenerator.Quad q = bb.quads.get(qi);

            // 处理右侧操作数：用 DAG 中已有的值替换
            String rarg1 = resolveVar(q.arg1, varMap);
            String rarg2 = resolveVar(q.arg2, varMap);

            // 跳过跳转/函数标记等非计算指令
            if (q.op.equals("J") || q.op.equals("J!=") || q.op.equals("FUNC")
                || q.op.equals("RET") || q.op.equals("EXIT")
                || q.op.equals("PARAM") || q.op.equals("CALL") || q.op.equals("READ")) {
                bb.dagLog.add("  [" + q + "] 非计算指令，跳过 DAG");
                continue;
            }

            String nodeKey = q.op + "|" + rarg1 + "|" + rarg2;

            DAGNode existing = nodeMap.get(nodeKey);
            if (existing != null) {
                // 公共子表达式！复用已有节点
                varMap.put(q.result, existing);
                existing.labels.add(q.result);
                eliminated++;
                bb.dagLog.add("  [" + q + "] ⚡ 公共子表达式消除: 复用 n" + existing.id + " " + existing.labels);
            } else {
                DAGNode node = new DAGNode(nodeId++, q.op, rarg1, rarg2);
                node.labels.add(q.result);
                dag.add(node);
                nodeMap.put(nodeKey, node);
                varMap.put(q.result, node);
                bb.dagLog.add("  [" + q + "] → n" + node.id + " " + node.labels);
            }
        }

        return eliminated;
    }

    private String resolveVar(String s, Map<String, DAGNode> varMap) {
        if (s == null || s.equals("_")) return "_";
        try { Integer.parseInt(s); return s; } catch (NumberFormatException ignored) {}
        DAGNode node = varMap.get(s);
        return node != null ? "n" + node.id : s;
    }

    // ==================== 输出 ====================

    private String buildFlowGraphText(List<BasicBlock> blocks) {
        StringBuilder sb = new StringBuilder();
        sb.append("========== 控制流图 (CFG) ==========\n");
        sb.append(String.format("基本块总数: %d, 四元式总数: %d\n\n", blocks.size(), quads.size()));

        for (BasicBlock bb : blocks) {
            sb.append(String.format("┌─ B%-3d [Q%02d → Q%02d]", bb.id, bb.startIdx, bb.endIdx));
            sb.append("  前驱: ");
            sb.append(bb.predecessors.isEmpty() ? "{}" : bb.predecessors.toString());
            sb.append("  后继: ");
            sb.append(bb.successors.isEmpty() ? "{}" : bb.successors.toString());
            sb.append("\n");

            for (int j = 0; j < bb.quads.size(); j++) {
                IRGenerator.Quad q = bb.quads.get(j);
                sb.append(String.format("│   Q%02d:  %s\n", bb.startIdx + j, q));
            }
            sb.append("└\n\n");
        }

        // 流图可达性分析
        sb.append("流图边:\n");
        for (BasicBlock bb : blocks) {
            for (int succ : bb.successors) {
                sb.append(String.format("  B%d → B%d\n", bb.id, succ));
            }
        }
        return sb.toString();
    }

    private String buildDAGSummary(List<BasicBlock> blocks) {
        StringBuilder sb = new StringBuilder();
        sb.append("========== DAG 局部优化摘要 ==========\n");
        int totalEliminated = 0;
        for (BasicBlock bb : blocks) {
            if (bb.dagLog.isEmpty()) continue;
            sb.append(String.format("B%d [Q%02d→Q%02d]:\n", bb.id, bb.startIdx, bb.endIdx));
            for (String log : bb.dagLog) {
                if (log.contains("公共子表达式消除")) totalEliminated++;
                sb.append(log).append("\n");
            }
            sb.append("\n");
        }
        sb.append("共消除公共子表达式: ").append(totalEliminated).append(" 条\n");
        return sb.toString();
    }

    private List<IRGenerator.Quad> rebuildQuads(List<BasicBlock> blocks) {
        List<IRGenerator.Quad> result = new ArrayList<>();
        for (BasicBlock bb : blocks) {
            result.addAll(bb.quads);
        }
        return result;
    }

    // ==================== 结果类 ====================

    public static class OptimizationResult {
        public final List<BasicBlock> blocks;
        public final String flowGraph;
        public final String dagSummary;
        public final List<IRGenerator.Quad> optimizedQuads;
        public final int eliminatedCount;

        OptimizationResult(List<BasicBlock> blocks, String flowGraph, String dagSummary,
                           List<IRGenerator.Quad> optimizedQuads, int eliminatedCount) {
            this.blocks = blocks;
            this.flowGraph = flowGraph;
            this.dagSummary = dagSummary;
            this.optimizedQuads = optimizedQuads;
            this.eliminatedCount = eliminatedCount;
        }
    }
}
