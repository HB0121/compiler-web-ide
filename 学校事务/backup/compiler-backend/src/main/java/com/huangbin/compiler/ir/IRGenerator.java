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
    private int tempCounter = 1; // 用于生成临时变量 t1, t2...

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
                // 变量声明，比如 int a = 10;
                // node.getValue() 是 "int a"
                String varName = node.getValue().split(" ")[1];
                if (!node.getChildren().isEmpty()) {
                    ASTNode expr = node.getChildren().get(0);
                    String val = evaluateExpr(expr);
                    quads.add(new Quad("=", val, "_", varName));
                }
                break;

            case "Assign":
                // 赋值语句，比如 b = a;
                // 第一个孩子是左值(b)，第二个孩子是右值表达式(a)
                if (node.getChildren().size() == 2) {
                    String target = node.getChildren().get(0).getValue();
                    String val = evaluateExpr(node.getChildren().get(1));
                    quads.add(new Quad("=", val, "_", target));
                }
                break;
        }
    }

    // 处理表达式并返回结果/变量名
    private String evaluateExpr(ASTNode expr) {
        if (expr.getName().equals("Literal") || expr.getName().equals("Identifier")) {
            return expr.getValue();
        }
        // 如果后续加入了加减乘除，这里会生成临时变量，比如：
        // String t = "t" + (tempCounter++);
        // quads.add(new Quad("+", arg1, arg2, t));
        // return t;
        return "_";
    }
}