package com.huangbin.compiler.ir;

import com.huangbin.compiler.model.ASTNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Stack;

public class IRGenerator {
    public static class Quad {
        public String op; public String arg1; public String arg2; public String result;
        public Quad(String op, String arg1, String arg2, String result) { this.op = op; this.arg1 = arg1; this.arg2 = arg2; this.result = result; }
        @Override public String toString() { return String.format("(%s, %s, %s, %s)", op, arg1, arg2, result); }
    }

    private static class LoopContext { public int condIdx; public int updateIdx; public List<Integer> breakList = new ArrayList<>(); public List<Integer> continueList = new ArrayList<>(); }

    private final List<Quad> quads = new ArrayList<>();
    private final Stack<LoopContext> loopStack = new Stack<>();
    private int tempCounter = 1;

    private int nextQuadIndex() { return quads.size(); }
    private void backpatch(int quadIndex, int targetIndex) { quads.get(quadIndex).result = String.valueOf(targetIndex); }

    public List<Quad> generate(ASTNode root) {
        if (root != null) { traverse(root); quads.add(new Quad("CALL", "main", "0", "_")); quads.add(new Quad("EXIT", "_", "_", "_")); }
        return quads;
    }

    private void traverse(ASTNode node) {
        if (node == null) return;
        switch (node.getName()) {
            case "Program": case "Compound":
                for (ASTNode child : node.getChildren()) traverse(child); break;
            case "FuncDecl":
                String[] parts = node.getValue().split(":");
                int skipJumpIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_")); 
                quads.add(new Quad("FUNC", parts[0], parts.length > 1 ? parts[1] : "", "_")); 
                if (!node.getChildren().isEmpty()) traverse(node.getChildren().get(0)); 
                quads.add(new Quad("RET", "0", "_", "_")); 
                backpatch(skipJumpIdx, nextQuadIndex()); break;
            case "ReturnStmt":
                quads.add(new Quad("RET", node.getChildren().isEmpty() ? "0" : evaluateExpr(node.getChildren().get(0)), "_", "_")); break;
            case "VarDecl":
                for (ASTNode child : node.getChildren()) {
                    if (child.getName().equals("Assign")) quads.add(new Quad("=", evaluateExpr(child.getChildren().get(1)), "_", child.getChildren().get(0).getValue()));
                    // 终极升级：提取数组声明指令 ALLOC
                    else if (child.getName().equals("ArrayDecl")) quads.add(new Quad("ALLOC", evaluateExpr(child.getChildren().get(0)), "_", child.getValue()));
                }
                break;
            case "FuncCall":
                String funcName = node.getValue();
                if (funcName.equals("write") && !node.getChildren().isEmpty()) {
                    ASTNode argNode = node.getChildren().get(0);
                    if (argNode.getName().equals("String")) quads.add(new Quad("CALL", "write_str", argNode.getValue(), "_"));
                    else quads.add(new Quad("CALL", "write", evaluateExpr(argNode), "_"));
                } else if (funcName.equals("read") && !node.getChildren().isEmpty()) {
                    // 支持 test5.4 的 read(n) 用法
                    quads.add(new Quad("READ", "_", "_", node.getChildren().get(0).getValue()));
                } else { evaluateExpr(node); }
                break;
            case "Assign":
                if (node.getChildren().size() == 2) {
                    ASTNode lhs = node.getChildren().get(0);
                    String rhsVal = evaluateExpr(node.getChildren().get(1));
                    // 终极升级：数组赋值指令 []=
                    if (lhs.getName().equals("ArrayAccess")) quads.add(new Quad("[]=", rhsVal, evaluateExpr(lhs.getChildren().get(0)), lhs.getValue()));
                    else quads.add(new Quad("=", rhsVal, "_", lhs.getValue()));
                }
                break;
            case "BreakStmt": if (!loopStack.isEmpty()) { int bIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_")); loopStack.peek().breakList.add(bIdx); } break;
            case "ContinueStmt": if (!loopStack.isEmpty()) { int cIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_")); loopStack.peek().continueList.add(cIdx); } break;
            case "IfStmt":
                String ifCond = evaluateExpr(node.getChildren().get(0));
                int jumpTrueIdx = nextQuadIndex(); quads.add(new Quad("J!=", ifCond, "0", "_")); 
                int jumpFalseIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_")); 
                backpatch(jumpTrueIdx, nextQuadIndex()); traverse(node.getChildren().get(1));
                int jumpEndIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_")); 
                backpatch(jumpFalseIdx, nextQuadIndex()); if (node.getChildren().size() > 2) traverse(node.getChildren().get(2)); backpatch(jumpEndIdx, nextQuadIndex()); 
                break;
            case "WhileStmt":
                LoopContext wCtx = new LoopContext(); wCtx.condIdx = nextQuadIndex(); loopStack.push(wCtx); 
                int wJumpTrueIdx = nextQuadIndex(); quads.add(new Quad("J!=", evaluateExpr(node.getChildren().get(0)), "0", "_")); 
                int wJumpEndIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_")); 
                backpatch(wJumpTrueIdx, nextQuadIndex()); traverse(node.getChildren().get(1)); 
                for (int idx : wCtx.continueList) backpatch(idx, wCtx.condIdx);
                quads.add(new Quad("J", "_", "_", String.valueOf(wCtx.condIdx))); 
                backpatch(wJumpEndIdx, nextQuadIndex()); for (int idx : wCtx.breakList) backpatch(idx, nextQuadIndex()); loopStack.pop(); break;
            case "DoWhileStmt":
                LoopContext dwCtx = new LoopContext(); int dwStartIdx = nextQuadIndex(); loopStack.push(dwCtx); traverse(node.getChildren().get(0)); 
                dwCtx.condIdx = nextQuadIndex(); for (int idx : dwCtx.continueList) backpatch(idx, dwCtx.condIdx);
                quads.add(new Quad("J!=", evaluateExpr(node.getChildren().get(1)), "0", String.valueOf(dwStartIdx))); 
                for (int idx : dwCtx.breakList) backpatch(idx, nextQuadIndex()); loopStack.pop(); break;
            case "ForStmt":
                traverse(node.getChildren().get(0)); LoopContext fCtx = new LoopContext(); fCtx.condIdx = nextQuadIndex(); loopStack.push(fCtx); 
                int fJumpTrueIdx = nextQuadIndex(); quads.add(new Quad("J!=", evaluateExpr(node.getChildren().get(1)), "0", "_")); 
                int fJumpEndIdx = nextQuadIndex(); quads.add(new Quad("J", "_", "_", "_")); 
                backpatch(fJumpTrueIdx, nextQuadIndex()); traverse(node.getChildren().get(3)); 
                fCtx.updateIdx = nextQuadIndex(); for (int idx : fCtx.continueList) backpatch(idx, fCtx.updateIdx);
                traverse(node.getChildren().get(2)); quads.add(new Quad("J", "_", "_", String.valueOf(fCtx.condIdx))); 
                backpatch(fJumpEndIdx, nextQuadIndex()); for (int idx : fCtx.breakList) backpatch(idx, nextQuadIndex()); loopStack.pop(); break;
        }
    }

    private String evaluateExpr(ASTNode expr) {
        if (expr == null) return "_"; if (expr.getName().equals("Literal") || expr.getName().equals("Identifier")) return expr.getValue();
        // 终极升级：数组读取指令 =[]
        if (expr.getName().equals("ArrayAccess")) {
            String resultTemp = "t" + (tempCounter++); quads.add(new Quad("=[]", expr.getValue(), evaluateExpr(expr.getChildren().get(0)), resultTemp)); return resultTemp;
        }
        if (expr.getName().equals("FuncCall")) {
            String funcName = expr.getValue();
            if (funcName.equals("read")) { String resultTemp = "t" + (tempCounter++); quads.add(new Quad("READ", "_", "_", resultTemp)); return resultTemp; }
            for (ASTNode arg : expr.getChildren()) quads.add(new Quad("PARAM", evaluateExpr(arg), "_", "_"));
            String resultTemp = "t" + (tempCounter++); quads.add(new Quad("CALL", funcName, String.valueOf(expr.getChildren().size()), resultTemp)); return resultTemp;
        }
        if (expr.getName().equals("UnaryOp")) { String resultTemp = "t" + (tempCounter++); quads.add(new Quad("-", "0", evaluateExpr(expr.getChildren().get(0)), resultTemp)); return resultTemp; }
        if (expr.getName().equals("BinOp") || expr.getName().equals("RelOp")) { String resultTemp = "t" + (tempCounter++); quads.add(new Quad(expr.getValue(), evaluateExpr(expr.getChildren().get(0)), evaluateExpr(expr.getChildren().get(1)), resultTemp)); return resultTemp; }
        return "_";
    }
}