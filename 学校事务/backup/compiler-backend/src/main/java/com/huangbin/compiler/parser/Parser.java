package com.huangbin.compiler.parser;

import com.huangbin.compiler.model.ASTNode;
import com.huangbin.compiler.model.Diagnostic;
import com.huangbin.compiler.model.Token;

import java.util.ArrayList;
import java.util.List;

public class Parser {

    private final List<Token> tokens;
    private int pos = 0;
    private final List<Diagnostic> diagnostics = new ArrayList<>();

    public Parser(List<Token> tokens) { this.tokens = tokens; }
    public List<Diagnostic> getDiagnostics() { return diagnostics; }

    private Token current() { return pos < tokens.size() ? tokens.get(pos) : null; }

    private Token matchText(String text) {
        Token curr = current();
        if (curr != null && curr.getText().equals(text)) {
            pos++; return curr;
        }
        return null;
    }

    private Token expectText(String text) {
        Token token = matchText(text);
        if (token == null) {
            Token curr = current();
            int line = curr != null ? curr.getLine() : (tokens.isEmpty() ? 1 : tokens.get(tokens.size() - 1).getLine());
            diagnostics.add(new Diagnostic("parser", line, "P001", "Expected '" + text + "'"));
        }
        return token;
    }

    // ================= 顶层解析：支持全局变量和函数 =================
    public ASTNode parseProgram() {
        ASTNode programNode = new ASTNode("Program");
        while (pos < tokens.size()) {
            Token curr = current();
            if (curr == null) break;

            String text = curr.getText();
            // 判断是否是声明语句 (变量或函数)
            if (text.equals("const") || text.equals("int") || text.equals("float") || text.equals("char") || text.equals("void")) {
                boolean isFunc = false;
                // 向前看(Lookahead)：找找有没有括号，判断是函数还是变量
                for (int i = pos; i < tokens.size(); i++) {
                    if (tokens.get(i).getText().equals("(")) { isFunc = true; break; }
                    if (tokens.get(i).getText().equals(";") || tokens.get(i).getText().equals("=")) { break; }
                }

                if (isFunc) {
                    ASTNode func = parseFuncDecl();
                    if (func != null) programNode.addChild(func);
                } else {
                    ASTNode var = parseVarDecl();
                    if (var != null) programNode.addChild(var);
                }
            } else {
                ASTNode stmt = parseStatement();
                if (stmt != null) programNode.addChild(stmt);
                else pos++;
            }
        }
        return programNode;
    }

    // 【新增】解析函数声明，完美复刻 PARSE204 和 PARSE225
    private ASTNode parseFuncDecl() {
        Token typeToken = current(); pos++; // void, int 等
        Token idToken = current();
        if (idToken != null && idToken.getKind().equals("identifier")) pos++;

        expectText("(");
        while (current() != null && !current().getText().equals(")")) pos++;
        expectText(")");

        ASTNode funcNode = new ASTNode("FuncDecl");
        funcNode.setValue(typeToken.getText() + " " + (idToken != null ? idToken.getText() : ""));

        Token brace = current();
        if (brace != null && brace.getText().equals("{")) {
            funcNode.addChild(parseCompoundStmt());
        } else {
            // 触发任务书要求的缺失代码块报错！
            diagnostics.add(new Diagnostic("parser", 0, "PARSE204", "Unknown: 代码块缺少左花括号"));
            diagnostics.add(new Diagnostic("parser", idToken != null ? idToken.getLine() : 0, "PARSE225", "函数 '" + (idToken != null ? idToken.getText() : "") + "' 缺少函数体"));
        }
        return funcNode;
    }

    // 【升级】解析变量声明，完美复刻 SEM301 常量初始化检查
    private ASTNode parseVarDecl() {
        boolean isConst = false;
        if (current() != null && current().getText().equals("const")) {
            isConst = true;
            pos++;
        }

        Token typeToken = current(); pos++;
        Token idToken = current();
        if (idToken != null && idToken.getKind().equals("identifier")) pos++;
        else { diagnostics.add(new Diagnostic("parser", typeToken.getLine(), "P003", "Expected id")); return null; }

        ASTNode varDeclNode = new ASTNode("VarDecl");
        varDeclNode.setValue((isConst ? "const " : "") + typeToken.getText() + " " + idToken.getText());

        if (matchText("=") != null) {
            varDeclNode.addChild(parseExpression());
        } else if (isConst) {
            // 触发任务书要求的常量未初始化语义报错！
            diagnostics.add(new Diagnostic("semantic", idToken.getLine(), "SEM301", "常量必须初始化: " + idToken.getText()));
        }

        expectText(";");
        return varDeclNode;
    }

    // ================= 以下为语句和表达式解析 (保持之前的完美版) =================
    private ASTNode parseStatement() {
        Token curr = current();
        if (curr == null) return null;
        String text = curr.getText();

        if (text.equals("const") || text.equals("int") || text.equals("float") || text.equals("char")) return parseVarDecl();
        if (text.equals("if")) return parseIfStmt();
        if (text.equals("while")) return parseWhileStmt();
        if (text.equals("{")) return parseCompoundStmt();
        if (curr.getKind().equals("identifier")) return parseAssignment();

        diagnostics.add(new Diagnostic("parser", curr.getLine(), "P002", "Unexpected token: " + text));
        pos++; return null;
    }

    private ASTNode parseCompoundStmt() {
        ASTNode compound = new ASTNode("Compound");
        expectText("{");
        while (current() != null && !current().getText().equals("}")) {
            ASTNode stmt = parseStatement();
            if (stmt != null) compound.addChild(stmt);
            else pos++;
        }
        expectText("}");
        return compound;
    }

    private ASTNode parseIfStmt() {
        ASTNode ifNode = new ASTNode("IfStmt");
        expectText("if"); expectText("(");
        ifNode.addChild(parseCondition());
        expectText(")");
        ifNode.addChild(parseStatement());
        if (matchText("else") != null) ifNode.addChild(parseStatement());
        return ifNode;
    }

    private ASTNode parseWhileStmt() {
        ASTNode whileNode = new ASTNode("WhileStmt");
        expectText("while"); expectText("(");
        whileNode.addChild(parseCondition());
        expectText(")");
        whileNode.addChild(parseStatement());
        return whileNode;
    }

    private ASTNode parseCondition() {
        ASTNode left = parseExpression();
        Token curr = current();
        if (curr != null && (curr.getText().equals(">") || curr.getText().equals("<") || curr.getText().equals("==") || curr.getText().equals("!="))) {
            ASTNode opNode = new ASTNode("RelOp");
            opNode.setValue(curr.getText()); opNode.setLine(curr.getLine()); pos++;
            opNode.addChild(left); opNode.addChild(parseExpression()); return opNode;
        }
        return left;
    }

    private ASTNode parseAssignment() {
        Token idToken = current(); pos++;
        ASTNode assignNode = new ASTNode("Assign"); assignNode.setValue("=");
        ASTNode idNode = new ASTNode("Identifier"); idNode.setValue(idToken.getText());
        assignNode.addChild(idNode);
        if (expectText("=") != null) assignNode.addChild(parseExpression());
        expectText(";");
        return assignNode;
    }

    private ASTNode parseExpression() {
        ASTNode left = parseTerm();
        if (left == null) return null;
        Token curr = current();
        while (curr != null && (curr.getText().equals("+") || curr.getText().equals("-"))) {
            pos++;
            ASTNode opNode = new ASTNode("BinOp"); opNode.setValue(curr.getText());
            ASTNode right = parseTerm();
            opNode.addChild(left); opNode.addChild(right);
            left = opNode; curr = current();
        }
        return left;
    }

    private ASTNode parseTerm() {
        ASTNode left = parseFactor();
        if (left == null) return null;
        Token curr = current();
        while (curr != null && (curr.getText().equals("*") || curr.getText().equals("/"))) {
            pos++;
            ASTNode opNode = new ASTNode("BinOp"); opNode.setValue(curr.getText());
            ASTNode right = parseFactor();
            opNode.addChild(left); opNode.addChild(right);
            left = opNode; curr = current();
        }
        return left;
    }

    private ASTNode parseFactor() {
        Token curr = current();
        if (curr == null) return null;
        if (curr.getKind().equals("int_literal") || curr.getKind().equals("float_literal")) {
            ASTNode node = new ASTNode("Literal"); node.setValue(curr.getText()); pos++; return node;
        } else if (curr.getKind().equals("identifier")) {
            ASTNode node = new ASTNode("Identifier"); node.setValue(curr.getText()); pos++; return node;
        } else if (matchText("(") != null) {
            ASTNode expr = parseExpression(); expectText(")"); return expr;
        }
        return null;
    }
}