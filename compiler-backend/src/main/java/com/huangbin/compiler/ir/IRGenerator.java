package com.huangbin.compiler.ir;

/** @author 黄彬 (12303070250) */

import com.huangbin.compiler.model.ASTNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Stack;

public class IRGenerator {
    public static class Quad {
        public String op; public String arg1; public String arg2; public String result;
        public Quad(String op, String arg1, String arg2, String result) {
            this.op = op; this.arg1 = arg1; this.arg2 = arg2; this.result = result;
        }
        @Override public String toString() { return String.format("(%s, %s, %s, %s)", op, arg1, arg2, result); }
    }

    private static class LoopContext {
        public int condIdx; public int updateIdx;
        public List<Integer> breakList = new ArrayList<>(); public List<Integer> continueList = new ArrayList<>();
    }

    private final List<Quad> quads = new ArrayList<>();
    private final Stack<LoopContext> loopStack = new Stack<>();
    private int tempCounter = 1;

    private int nextQuadIndex() { return quads.size(); }
    private void backpatch(int quadIndex, int targetIndex) { quads.get(quadIndex).result = String.valueOf(targetIndex); }

    public List<Quad> generate(ASTNode root) {
        if (root != null) {
            traverse(root);
            // 自动注入启动主函数的胶水代码
            quads.add(new Quad("CALL", "main", "0", "_"));
            quads.add(new Quad("EXIT", "_", "_", "_")); // 程序完美收尾
        }
        return quads;
    }

    private void traverse(ASTNode node) {
        if (node == null) return;
        switch (node.getName()) {
            case "Program":
            case "Compound":
                for (ASTNode child : node.getChildren()) traverse(child);
                break;

            // 【核心升级】：处理函数定义块
            case "FuncDecl":
                String[] parts = node.getValue().split(":");
                String name = parts[0];
                String params = parts.length > 1 ? parts[1] : "";

                int skipJumpIdx = nextQuadIndex();
                quads.add(new Quad("J", "_", "_", "_")); // 遇到函数定义，直接跳过其内部代码

                quads.add(new Quad("FUNC", name, params, "_")); // 标记函数入口
                if (!node.getChildren().isEmpty()) traverse(node.getChildren().get(0)); // 生成函数体
                quads.add(new Quad("RET", "0", "_", "_")); // 兜底的默认 return 0

                backpatch(skipJumpIdx, nextQuadIndex()); // 回填跳过位置
                break;

            case "ReturnStmt":
                String retVal = "0";
                if (!node.getChildren().isEmpty()) retVal = evaluateExpr(node.getChildren().get(0));
                quads.add(new Quad("RET", retVal, "_", "_"));
                break;

            case "VarDecl":
                for (ASTNode child : node.getChildren()) {
                    if (child.getName().equals("Assign")) {
                        String target = child.getChildren().get(0).getValue();
                        String val = evaluateExpr(child.getChildren().get(1));
                        quads.add(new Quad("=", val, "_", target));
                    }
                }
                break;

            case "FuncCall":
                String funcName = node.getValue();
                if (funcName.equals("write") && !node.getChildren().isEmpty()) {
                    ASTNode argNode = node.getChildren().get(0);
                    if (argNode.getName().equals("String")) quads.add(new Quad("CALL", "write_str", argNode.getValue(), "_"));
                    else quads.add(new Quad("CALL", "write", evaluateExpr(argNode), "_"));
                } else {
                    evaluateExpr(node); // 单独作为语句的普通函数调用
                }
                break;

            case "Assign":
                if (node.getChildren().size() == 2) {
                    quads.add(new Quad("=", evaluateExpr(node.getChildren().get(1)), "_", node.getChildren().get(0).getValue()));
                }
                break;

            case "BreakStmt":
                if (!loopStack.isEmpty()) {
                    int bIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_")); loopStack.peek().breakList.add(bIdx);
                }
                break;

            case "ContinueStmt":
                if (!loopStack.isEmpty()) {
                    int cIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_")); loopStack.peek().continueList.add(cIdx);
                }
                break;

            case "IfStmt":
                String ifCond = evaluateExpr(node.getChildren().get(0));
                int jumpTrueIdx = nextQuadIndex(); quads.add(new Quad("J!=", ifCond, "0", "_"));
                int jumpFalseIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_"));
                backpatch(jumpTrueIdx, nextQuadIndex()); traverse(node.getChildren().get(1));
                int jumpEndIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_"));
                backpatch(jumpFalseIdx, nextQuadIndex());
                if (node.getChildren().size() > 2) traverse(node.getChildren().get(2));
                backpatch(jumpEndIdx, nextQuadIndex());
                break;

            case "WhileStmt":
                LoopContext wCtx = new LoopContext(); wCtx.condIdx = nextQuadIndex(); loopStack.push(wCtx);
                String wCond = evaluateExpr(node.getChildren().get(0));
                int wJumpTrueIdx = nextQuadIndex(); quads.add(new Quad("J!=", wCond, "0", "_"));
                int wJumpEndIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_"));
                backpatch(wJumpTrueIdx, nextQuadIndex()); traverse(node.getChildren().get(1));
                for (int idx : wCtx.continueList) backpatch(idx, wCtx.condIdx);
                quads.add(new Quad("J", "_", "_", String.valueOf(wCtx.condIdx)));
                backpatch(wJumpEndIdx, nextQuadIndex()); for (int idx : wCtx.breakList) backpatch(idx, nextQuadIndex());
                loopStack.pop();
                break;

            case "DoWhileStmt":
                LoopContext dwCtx = new LoopContext(); int dwStartIdx = nextQuadIndex(); loopStack.push(dwCtx);
                traverse(node.getChildren().get(0));
                dwCtx.condIdx = nextQuadIndex(); for (int idx : dwCtx.continueList) backpatch(idx, dwCtx.condIdx);
                String dwCond = evaluateExpr(node.getChildren().get(1));
                quads.add(new Quad("J!=", dwCond, "0", String.valueOf(dwStartIdx)));
                for (int idx : dwCtx.breakList) backpatch(idx, nextQuadIndex());
                loopStack.pop();
                break;

            case "ForStmt":
                traverse(node.getChildren().get(0)); LoopContext fCtx = new LoopContext(); fCtx.condIdx = nextQuadIndex(); loopStack.push(fCtx);
                String fCond = evaluateExpr(node.getChildren().get(1));
                int fJumpTrueIdx = nextQuadIndex(); quads.add(new Quad("J!=", fCond, "0", "_"));
                int fJumpEndIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_"));
                backpatch(fJumpTrueIdx, nextQuadIndex()); traverse(node.getChildren().get(3));
                fCtx.updateIdx = nextQuadIndex(); for (int idx : fCtx.continueList) backpatch(idx, fCtx.updateIdx);
                traverse(node.getChildren().get(2)); quads.add(new Quad("J", "_", "_", String.valueOf(fCtx.condIdx)));
                backpatch(fJumpEndIdx, nextQuadIndex()); for (int idx : fCtx.breakList) backpatch(idx, nextQuadIndex());
                loopStack.pop();
                break;
        }
    }

    private String evaluateExpr(ASTNode expr) {
        if (expr == null) return "_";
        if (expr.getName().equals("Literal") || expr.getName().equals("Identifier")) return expr.getValue();

        // 【核心升级】：把函数调用转化为 PARAM 和 CALL 指令序列
        if (expr.getName().equals("FuncCall")) {
            String funcName = expr.getValue();
            if (funcName.equals("read")) {
                String resultTemp = "t" + (tempCounter++); quads.add(new Quad("READ", "_", "_", resultTemp)); return resultTemp;
            }
            // 提取参数并逐个压入参数准备区
            for (ASTNode arg : expr.getChildren()) {
                quads.add(new Quad("PARAM", evaluateExpr(arg), "_", "_"));
            }
            String resultTemp = "t" + (tempCounter++);
            quads.add(new Quad("CALL", funcName, String.valueOf(expr.getChildren().size()), resultTemp));
            return resultTemp;
        }

        if (expr.getName().equals("UnaryOp")) {
            String arg = evaluateExpr(expr.getChildren().get(0)); String resultTemp = "t" + (tempCounter++); quads.add(new Quad("-", "0", arg, resultTemp)); return resultTemp;
        }
        if (expr.getName().equals("BinOp") || expr.getName().equals("RelOp")) {
            String arg1 = evaluateExpr(expr.getChildren().get(0)); String arg2 = evaluateExpr(expr.getChildren().get(1)); String resultTemp = "t" + (tempCounter++); quads.add(new Quad(expr.getValue(), arg1, arg2, resultTemp)); return resultTemp;
        }
        return "_";
    }
}