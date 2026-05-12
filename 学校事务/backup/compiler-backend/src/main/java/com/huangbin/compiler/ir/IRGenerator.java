package com.huangbin.compiler.ir;

import com.huangbin.compiler.model.ASTNode;

import java.util.ArrayList;
import java.util.List;

public class IRGenerator {

    // 内部类：四元式结构
    public static class Quad {
        public String op;
        public String arg1;
        public String arg2;
        public String result;

        public Quad(String op, String arg1, String arg2, String result) {
            this.op = op;
            this.arg1 = arg1;
            this.arg2 = arg2;
            this.result = result;
        }

        @Override
        public String toString() {
            return String.format("(%s, %s, %s, %s)", op, arg1, arg2, result);
        }
    }

    private final List<Quad> quads = new ArrayList<>();
    private int tempCounter = 1; // 用于生成临时变量 t1, t2, t3...

    // 暴露给外部调用的主入口
    public List<Quad> generate(ASTNode root) {
        if (root != null) {
            traverse(root);
        }
        return quads;
    }

    // 递归遍历 AST 树
    private void traverse(ASTNode node) {
        if (node == null) return;

        switch (node.getName()) {
            case "Program":
                for (ASTNode child : node.getChildren()) {
                    traverse(child);
                }
                break;

            case "VarDecl":
                // 变量声明，比如 int a = 10; 或 int c = a + b * 2;
                // node.getValue() 是 "int a"
                String varName = node.getValue().split(" ")[1];
                if (!node.getChildren().isEmpty()) {
                    ASTNode expr = node.getChildren().get(0);
                    // 核心：调用 evaluateExpr 去处理等号右边的复杂表达式
                    String val = evaluateExpr(expr);
                    quads.add(new Quad("=", val, "_", varName));
                }
                break;

            case "Assign":
                // 赋值语句，比如 b = a; 或 d = (a + b) * 2;
                if (node.getChildren().size() == 2) {
                    String target = node.getChildren().get(0).getValue();
                    // 核心：调用 evaluateExpr 去处理等号右边的复杂表达式
                    String val = evaluateExpr(node.getChildren().get(1));
                    quads.add(new Quad("=", val, "_", target));
                }
                break;
        }
    }

    // ================== 增强版：递归处理算术表达式 ==================
    // 处理表达式并返回结果/变量名
    private String evaluateExpr(ASTNode expr) {
        if (expr == null) return "_";

        // 1. 如果是叶子节点（纯数字或已有的变量名），直接返回它的值
        if (expr.getName().equals("Literal") || expr.getName().equals("Identifier")) {
            return expr.getValue();
        }

        // 2. 如果是二元操作符 (+, -, *, /)
        if (expr.getName().equals("BinOp")) {
            String op = expr.getValue();

            // 递归算出左边和右边的结果（这会层层深入，优先处理树底层的乘除法或括号里的内容）
            String arg1 = evaluateExpr(expr.getChildren().get(0));
            String arg2 = evaluateExpr(expr.getChildren().get(1));

            // 申请一个新的临时变量存放这次加减乘除的计算结果，比如 t1, t2
            String resultTemp = "t" + (tempCounter++);

            // 生成一条计算用的四元式，例如 (+, a, b, t1)
            quads.add(new Quad(op, arg1, arg2, resultTemp));

            // 返回这个临时变量名，供更上层的加减乘除继续使用
            return resultTemp;
        }

        return "_";
    }
}