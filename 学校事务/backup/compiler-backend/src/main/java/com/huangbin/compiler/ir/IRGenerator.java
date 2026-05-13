package com.huangbin.compiler.ir;

import com.huangbin.compiler.model.ASTNode;

import java.util.ArrayList;
import java.util.List;

public class IRGenerator {

    // 内部类：四元式结构
    public static class Quad {
        public String op; public String arg1; public String arg2; public String result;
        public Quad(String op, String arg1, String arg2, String result) {
            this.op = op; this.arg1 = arg1; this.arg2 = arg2; this.result = result;
        }
        @Override public String toString() { return String.format("(%s, %s, %s, %s)", op, arg1, arg2, result); }
    }

    private final List<Quad> quads = new ArrayList<>();
    private int tempCounter = 1;

    // 获取下一条四元式的行号
    private int nextQuadIndex() { return quads.size(); }

    // 回填技术：把目标行号填入指定的跳转指令中
    private void backpatch(int quadIndex, int targetIndex) {
        quads.get(quadIndex).result = String.valueOf(targetIndex);
    }

    public List<Quad> generate(ASTNode root) {
        if (root != null) traverse(root);
        return quads;
    }

    private void traverse(ASTNode node) {
        if (node == null) return;

        switch (node.getName()) {
            case "Program":
            case "Compound":
            case "FuncDecl": // 【新增】支持扒开 main() 函数的外壳，直接解析里面的代码块
                for (ASTNode child : node.getChildren()) traverse(child);
                break;

            case "VarDecl":
                // 【升级】支持连续声明，例如 int x, y=3, z;
                for (ASTNode child : node.getChildren()) {
                    if (child.getName().equals("Assign")) {
                        String target = child.getChildren().get(0).getValue();
                        String val = evaluateExpr(child.getChildren().get(1));
                        quads.add(new Quad("=", val, "_", target));
                    }
                    // 如果只是声明没有赋值（如 int x;），在四元式中可以直接忽略，等待后续赋值
                }
                break;

            case "FuncCall":
                // 【新增】处理函数调用，例如 write(x);
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
                // 处理条件
                ASTNode ifCond = node.getChildren().get(0);
                String ifOp = ifCond.getValue();
                String ifArg1 = evaluateExpr(ifCond.getChildren().get(0));
                String ifArg2 = evaluateExpr(ifCond.getChildren().get(1));

                int jumpTrueIdx = nextQuadIndex();
                quads.add(new Quad("J" + ifOp, ifArg1, ifArg2, "_")); // 满足条件跳向 True分支

                int jumpFalseIdx = nextQuadIndex();
                quads.add(new Quad("J", "_", "_", "_")); // 否则无条件跳向 False分支

                // True 分支
                backpatch(jumpTrueIdx, nextQuadIndex());
                traverse(node.getChildren().get(1));

                int jumpEndIdx = nextQuadIndex();
                quads.add(new Quad("J", "_", "_", "_")); // True分支执行完跳出 if

                // False 分支 (如果有 else)
                backpatch(jumpFalseIdx, nextQuadIndex());
                if (node.getChildren().size() > 2) {
                    traverse(node.getChildren().get(2));
                }
                backpatch(jumpEndIdx, nextQuadIndex()); // 回填跳出位置
                break;

            case "WhileStmt":
                int startIdx = nextQuadIndex(); // 记录循环开始的位置

                // 处理条件
                ASTNode wCond = node.getChildren().get(0);
                String wOp = wCond.getValue();
                String wArg1 = evaluateExpr(wCond.getChildren().get(0));
                String wArg2 = evaluateExpr(wCond.getChildren().get(1));

                int wJumpTrueIdx = nextQuadIndex();
                quads.add(new Quad("J" + wOp, wArg1, wArg2, "_")); // 满足条件进入循环体

                int wJumpEndIdx = nextQuadIndex();
                quads.add(new Quad("J", "_", "_", "_")); // 否则跳出循环

                // 循环体
                backpatch(wJumpTrueIdx, nextQuadIndex());
                traverse(node.getChildren().get(1));
                quads.add(new Quad("J", "_", "_", String.valueOf(startIdx))); // 循环体结束，无条件跳回开头

                // 循环结束点
                backpatch(wJumpEndIdx, nextQuadIndex());
                break;
        }
    }

    private String evaluateExpr(ASTNode expr) {
        if (expr == null) return "_";
        if (expr.getName().equals("Literal") || expr.getName().equals("Identifier")) return expr.getValue();
        if (expr.getName().equals("BinOp")) {
            String arg1 = evaluateExpr(expr.getChildren().get(0));
            String arg2 = evaluateExpr(expr.getChildren().get(1));
            String resultTemp = "t" + (tempCounter++);
            quads.add(new Quad(expr.getValue(), arg1, arg2, resultTemp));
            return resultTemp;
        }
        return "_";
    }
}