package com.huangbin.compiler.ir;

import com.huangbin.compiler.model.ASTNode;
import java.util.ArrayList;
import java.util.List;

public class IRGenerator {
    public static class Quad {
        public String op; public String arg1; public String arg2; public String result;
        public Quad(String op, String arg1, String arg2, String result) {
            this.op = op; this.arg1 = arg1; this.arg2 = arg2; this.result = result;
        }
        @Override public String toString() { return String.format("(%s, %s, %s, %s)", op, arg1, arg2, result); }
    }

    private final List<Quad> quads = new ArrayList<>();
    private int tempCounter = 1;

    private int nextQuadIndex() { return quads.size(); }
    private void backpatch(int quadIndex, int targetIndex) { quads.get(quadIndex).result = String.valueOf(targetIndex); }

    public List<Quad> generate(ASTNode root) {
        if (root != null) traverse(root);
        return quads;
    }

    private void traverse(ASTNode node) {
        if (node == null) return;
        switch (node.getName()) {
            case "Program":
            case "Compound":
            case "FuncDecl":
                for (ASTNode child : node.getChildren()) traverse(child);
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
                String arg = evaluateExpr(node.getChildren().get(0));
                quads.add(new Quad("CALL", funcName, arg, "_"));
                break;
            case "Assign":
                if (node.getChildren().size() == 2) {
                    quads.add(new Quad("=", evaluateExpr(node.getChildren().get(1)), "_", node.getChildren().get(0).getValue()));
                }
                break;
            case "IfStmt":
                // 【精简架构】所有条件都算作一个临时变量，判断 != 0 即可
                String ifCond = evaluateExpr(node.getChildren().get(0));
                int jumpTrueIdx = nextQuadIndex();
                quads.add(new Quad("J!=", ifCond, "0", "_"));

                int jumpFalseIdx = nextQuadIndex();
                quads.add(new Quad("J", "_", "_", "_"));

                backpatch(jumpTrueIdx, nextQuadIndex());
                traverse(node.getChildren().get(1));

                int jumpEndIdx = nextQuadIndex();
                quads.add(new Quad("J", "_", "_", "_"));

                backpatch(jumpFalseIdx, nextQuadIndex());
                if (node.getChildren().size() > 2) traverse(node.getChildren().get(2));
                backpatch(jumpEndIdx, nextQuadIndex());
                break;

            case "WhileStmt":
                int startIdx = nextQuadIndex();
                String wCond = evaluateExpr(node.getChildren().get(0));

                int wJumpTrueIdx = nextQuadIndex();
                quads.add(new Quad("J!=", wCond, "0", "_"));

                int wJumpEndIdx = nextQuadIndex();
                quads.add(new Quad("J", "_", "_", "_"));

                backpatch(wJumpTrueIdx, nextQuadIndex());
                traverse(node.getChildren().get(1));
                quads.add(new Quad("J", "_", "_", String.valueOf(startIdx)));
                backpatch(wJumpEndIdx, nextQuadIndex());
                break;
        }
    }

    private String evaluateExpr(ASTNode expr) {
        if (expr == null) return "_";
        if (expr.getName().equals("Literal") || expr.getName().equals("Identifier")) return expr.getValue();

        // 【新增】处理负数： 0 - arg
        if (expr.getName().equals("UnaryOp")) {
            String arg = evaluateExpr(expr.getChildren().get(0));
            String resultTemp = "t" + (tempCounter++);
            quads.add(new Quad("-", "0", arg, resultTemp));
            return resultTemp;
        }

        // 处理二元和关系运算
        if (expr.getName().equals("BinOp") || expr.getName().equals("RelOp")) {
            String arg1 = evaluateExpr(expr.getChildren().get(0));
            String arg2 = evaluateExpr(expr.getChildren().get(1));
            String resultTemp = "t" + (tempCounter++);
            quads.add(new Quad(expr.getValue(), arg1, arg2, resultTemp));
            return resultTemp;
        }
        return "_";
    }
}