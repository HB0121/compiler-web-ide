package com.huangbin.compiler.parser;

import com.huangbin.compiler.model.ASTNode;
import com.huangbin.compiler.model.Diagnostic;
import com.huangbin.compiler.model.Token;

import java.util.ArrayList;
import java.util.List;

public class Parser {

    // 辅助打印树结构的方法
    private static void printAST(ASTNode node, int depth) {
        if (node == null) return;
        String indent = "  ".repeat(Math.max(0, depth));
        System.out.println(indent + "Node: " + node.getName() + " (Value: " + node.getValue() + ")");
        for (ASTNode child : node.getChildren()) {
            printAST(child, depth + 1);
        }
    }

    private final List<Token> tokens;
    private int pos = 0;
    private final List<Diagnostic> diagnostics = new ArrayList<>();

    public Parser(List<Token> tokens) {
        this.tokens = tokens;
    }

    public List<Diagnostic> getDiagnostics() {
        return diagnostics;
    }

    // 辅助方法：获取当前 Token
    private Token current() {
        if (pos < tokens.size()) {
            return tokens.get(pos);
        }
        return null;
    }

    // 辅助方法：匹配特定文本，若匹配则游标前进
    private Token matchText(String text) {
        Token currentToken = current();
        if (currentToken != null && currentToken.getText().equals(text)) {
            pos++;
            return currentToken;
        }
        return null;
    }

    // 辅助方法：期望匹配特定文本，若失败则记录错误
    private Token expectText(String text) {
        Token token = matchText(text);
        if (token == null) {
            Token currentToken = current();
            int line = currentToken != null ? currentToken.getLine() : (tokens.isEmpty() ? 1 : tokens.get(tokens.size() - 1).getLine());
            diagnostics.add(new Diagnostic("parser", line, "P001", "Expected '" + text + "'"));
        }
        return token;
    }

    // ------------------- 语法规则解析 -------------------

    // 程序的入口：Program -> { Statement }
    public ASTNode parseProgram() {
        ASTNode programNode = new ASTNode("Program");
        while (pos < tokens.size()) {
            ASTNode stmt = parseStatement();
            if (stmt != null) {
                programNode.addChild(stmt);
            } else {
                // 如果解析失败，为了避免死循环，强行跳过一个 Token
                pos++;
            }
        }
        return programNode;
    }

    // 语句解析分流器
    private ASTNode parseStatement() {
        Token curr = current();
        if (curr == null) return null;

        String text = curr.getText();
        if (text.equals("int") || text.equals("float") || text.equals("char")) {
            return parseVarDecl();
        } else if (curr.getKind().equals("identifier")) {
            // 这里为了简化，我们假设以标识符开头的都是赋值语句 (例如 x = 10;)
            return parseAssignment();
        } else {
            // 遇到不认识的语句类型，暂时跳过并报错
            int line = curr.getLine();
            diagnostics.add(new Diagnostic("parser", line, "P002", "Unexpected token: " + text));
            pos++;
            return null;
        }
    }

    // 解析变量声明：Type Identifier [ = Expression ] ;
    private ASTNode parseVarDecl() {
        Token typeToken = current(); // int, float, etc.
        pos++; // 消耗类型 Token

        Token idToken = current();
        if (idToken != null && idToken.getKind().equals("identifier")) {
            pos++; // 消耗标识符
        } else {
            diagnostics.add(new Diagnostic("parser", typeToken.getLine(), "P003", "Expected identifier after type"));
            return null;
        }

        ASTNode varDeclNode = new ASTNode("VarDecl");
        varDeclNode.setValue(typeToken.getText() + " " + idToken.getText());
        varDeclNode.setLine(idToken.getLine());

        // 检查是否有初始化赋值
        if (matchText("=") != null) {
            ASTNode expr = parseExpression();
            varDeclNode.addChild(expr);
        }

        expectText(";");
        return varDeclNode;
    }

    // 解析赋值语句：Identifier = Expression ;
    private ASTNode parseAssignment() {
        Token idToken = current();
        pos++; // 消耗标识符

        ASTNode assignNode = new ASTNode("Assign");
        assignNode.setValue("=");
        assignNode.setLine(idToken.getLine());

        ASTNode idNode = new ASTNode("Identifier");
        idNode.setValue(idToken.getText());
        idNode.setLine(idToken.getLine());
        assignNode.addChild(idNode);

        if (expectText("=") != null) {
            ASTNode expr = parseExpression();
            assignNode.addChild(expr);
        }

        expectText(";");
        return assignNode;
    }

    // ================== 增强版表达式解析 (支持加减乘除和括号) ==================

    // 解析加减法表达式: Term { (+ | -) Term }
    private ASTNode parseExpression() {
        ASTNode left = parseTerm();
        if (left == null) return null;

        Token curr = current();
        while (curr != null && (curr.getText().equals("+") || curr.getText().equals("-"))) {
            pos++; // 消耗运算符
            ASTNode opNode = new ASTNode("BinOp");
            opNode.setValue(curr.getText());
            opNode.setLine(curr.getLine());

            ASTNode right = parseTerm();
            if (right == null) {
                diagnostics.add(new Diagnostic("parser", curr.getLine(), "P005", "Expected term after " + curr.getText()));
                break;
            }

            opNode.addChild(left);
            opNode.addChild(right);
            left = opNode; // 将新构建的节点作为下一轮循环的左节点
            curr = current();
        }
        return left;
    }

    // 解析乘除法项: Factor { (* | /) Factor }
    private ASTNode parseTerm() {
        ASTNode left = parseFactor();
        if (left == null) return null;

        Token curr = current();
        while (curr != null && (curr.getText().equals("*") || curr.getText().equals("/"))) {
            pos++;
            ASTNode opNode = new ASTNode("BinOp");
            opNode.setValue(curr.getText());
            opNode.setLine(curr.getLine());

            ASTNode right = parseFactor();
            if (right == null) {
                diagnostics.add(new Diagnostic("parser", curr.getLine(), "P006", "Expected factor after " + curr.getText()));
                break;
            }

            opNode.addChild(left);
            opNode.addChild(right);
            left = opNode;
            curr = current();
        }
        return left;
    }

    // 解析基础因子: 标识符 或 字面量 或 (表达式)
    private ASTNode parseFactor() {
        Token curr = current();
        if (curr == null) return null;

        if (curr.getKind().equals("int_literal") || curr.getKind().equals("float_literal")) {
            ASTNode literalNode = new ASTNode("Literal");
            literalNode.setValue(curr.getText());
            literalNode.setLine(curr.getLine());
            pos++;
            return literalNode;
        } else if (curr.getKind().equals("identifier")) {
            ASTNode idNode = new ASTNode("Identifier");
            idNode.setValue(curr.getText());
            idNode.setLine(curr.getLine());
            pos++;
            return idNode;
        } else if (matchText("(") != null) {
            // 处理括号优先级
            ASTNode expr = parseExpression();
            expectText(")");
            return expr;
        }

        diagnostics.add(new Diagnostic("parser", curr.getLine(), "P004", "Expected expression"));
        return null;
    }
}