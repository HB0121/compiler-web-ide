package com.huangbin.compiler.parser;

import com.huangbin.compiler.model.ASTNode;
import com.huangbin.compiler.model.Diagnostic;
import com.huangbin.compiler.model.Token;
import java.util.ArrayList;
import java.util.List;

public class Parser {
    private final List<Token> tokens; private int pos = 0;
    private final List<Diagnostic> diagnostics = new ArrayList<>();
    public Parser(List<Token> tokens) { this.tokens = tokens; }
    public List<Diagnostic> getDiagnostics() { return diagnostics; }
    private Token current() { return pos < tokens.size() ? tokens.get(pos) : null; }
    private Token matchText(String text) { Token curr = current(); if (curr != null && curr.getText().equals(text)) { pos++; return curr; } return null; }
    private Token expectText(String text) {
        Token token = matchText(text);
        if (token == null) diagnostics.add(new Diagnostic("parser", current() != null ? current().getLine() : 0, "P001", "Expected '" + text + "'"));
        return token;
    }

    public ASTNode parseProgram() {
        ASTNode programNode = new ASTNode("Program");
        while (pos < tokens.size()) {
            Token curr = current(); if (curr == null) break;
            String text = curr.getText();
            if (text.equals("const") || text.equals("int") || text.equals("float") || text.equals("char") || text.equals("void")) {
                boolean isFunc = false;
                for (int i = pos; i < tokens.size(); i++) {
                    if (tokens.get(i).getText().equals("(")) { isFunc = true; break; }
                    if (tokens.get(i).getText().equals(";") || tokens.get(i).getText().equals("=") || tokens.get(i).getText().equals(",") || tokens.get(i).getText().equals("[")) { break; }
                }
                if (isFunc) { ASTNode func = parseFuncDecl(); if (func != null) programNode.addChild(func); } 
                else { ASTNode var = parseVarDecl(); if (var != null) programNode.addChild(var); }
            } else if (text.equals("main")) { ASTNode func = parseFuncDecl(); if (func != null) programNode.addChild(func);
            } else { ASTNode stmt = parseStatement(); if (stmt != null) programNode.addChild(stmt); else pos++; }
        }
        return programNode;
    }

    private ASTNode parseFuncDecl() {
        String typeStr = current().getText(); pos++; Token idToken = current();
        if (idToken != null && (idToken.getKind().equals("identifier") || idToken.getText().equals("main"))) pos++;
        expectText("("); List<String> params = new ArrayList<>();
        while (current() != null && !current().getText().equals(")")) {
            String pType = current().getText(); pos++;
            if (pType.equals("void")) break; // 兼容 main(void)
            if (current() != null && current().getKind().equals("identifier")) { params.add(current().getText()); pos++; }
            if (matchText(",") == null) break;
        }
        expectText(")"); if (matchText(";") != null) return null; 
        ASTNode funcNode = new ASTNode("FuncDecl");
        funcNode.setValue((idToken != null ? idToken.getText() : "main") + ":" + String.join(",", params));
        if (current() != null && current().getText().equals("{")) funcNode.addChild(parseCompoundStmt());
        return funcNode;
    }

    private ASTNode parseVarDecl() {
        boolean isConst = matchText("const") != null; Token typeToken = current(); pos++;
        ASTNode varDeclNode = new ASTNode("VarDecl"); varDeclNode.setValue((isConst ? "const " : "") + typeToken.getText());
        while (current() != null) {
            Token idToken = current();
            if (idToken != null && idToken.getKind().equals("identifier")) pos++; else break;
            
            // 终极升级：解析数组声明 int a[50];
            if (matchText("[") != null) {
                ASTNode arrayDecl = new ASTNode("ArrayDecl"); arrayDecl.setValue(idToken.getText());
                arrayDecl.addChild(parseLogical()); expectText("]"); varDeclNode.addChild(arrayDecl);
            } else {
                ASTNode idNode = new ASTNode("Identifier"); idNode.setValue(idToken.getText());
                if (matchText("=") != null) {
                    ASTNode assign = new ASTNode("Assign"); assign.addChild(idNode); assign.addChild(parseLogical()); varDeclNode.addChild(assign);
                } else varDeclNode.addChild(idNode);
            }
            if (matchText(",") == null) break;
        }
        expectText(";"); return varDeclNode;
    }

    private ASTNode parseStatement() {
        Token curr = current(); if (curr == null) return null; String text = curr.getText();
        if (text.equals("break")) { pos++; expectText(";"); return new ASTNode("BreakStmt"); }
        if (text.equals("continue")) { pos++; expectText(";"); return new ASTNode("ContinueStmt"); }
        if (text.equals("do")) return parseDoWhileStmt();
        if (text.equals("return")) {
            pos++; ASTNode retNode = new ASTNode("ReturnStmt");
            if (current() != null && !current().getText().equals(";")) retNode.addChild(parseLogical());
            expectText(";"); return retNode;
        }
        if (text.equals("const") || text.equals("int") || text.equals("float") || text.equals("char")) return parseVarDecl();
        if (text.equals("if")) return parseIfStmt(); if (text.equals("while")) return parseWhileStmt();
        if (text.equals("for")) return parseForStmt(); if (text.equals("{")) return parseCompoundStmt();
        
        if (curr.getKind().equals("identifier") || text.equals("write") || text.equals("read")) {
            if (pos + 1 < tokens.size() && tokens.get(pos + 1).getText().equals("(")) {
                Token idToken = current(); pos++; ASTNode callNode = parseFuncCall(idToken); expectText(";"); return callNode;
            }
            return parseAssignment();
        }
        diagnostics.add(new Diagnostic("parser", curr.getLine(), "P002", "Unexpected token: " + text)); pos++; return null;
    }

    private ASTNode parseDoWhileStmt() { ASTNode doNode = new ASTNode("DoWhileStmt"); expectText("do"); doNode.addChild(parseCompoundStmt()); expectText("while"); expectText("("); doNode.addChild(parseLogical()); expectText(")"); expectText(";"); return doNode; }
    private ASTNode parseForStmt() { ASTNode forNode = new ASTNode("ForStmt"); expectText("for"); expectText("("); forNode.addChild(parseAssignmentInner()); expectText(";"); forNode.addChild(parseLogical()); expectText(";"); forNode.addChild(parseAssignmentInner()); expectText(")"); forNode.addChild(parseStatement()); return forNode; }

    private ASTNode parseAssignmentInner() {
        Token idToken = current(); pos++; ASTNode lhsNode;
        // 终极升级：解析数组寻址赋值 a[i] = 10;
        if (matchText("[") != null) {
            lhsNode = new ASTNode("ArrayAccess"); lhsNode.setValue(idToken.getText());
            lhsNode.addChild(parseLogical()); expectText("]");
        } else {
            lhsNode = new ASTNode("Identifier"); lhsNode.setValue(idToken.getText());
        }

        // 终极升级：解析自增操作 i++ => i = i + 1
        if (current() != null && (current().getText().equals("++") || current().getText().equals("--"))) {
            String op = current().getText(); pos++;
            ASTNode assignNode = new ASTNode("Assign"); assignNode.setValue("="); assignNode.addChild(lhsNode);
            ASTNode binOp = new ASTNode("BinOp"); binOp.setValue(op.equals("++") ? "+" : "-");
            binOp.addChild(lhsNode); ASTNode oneNode = new ASTNode("Literal"); oneNode.setValue("1"); binOp.addChild(oneNode);
            assignNode.addChild(binOp); return assignNode;
        }

        ASTNode assignNode = new ASTNode("Assign"); assignNode.setValue("="); assignNode.addChild(lhsNode);
        if (expectText("=") != null) assignNode.addChild(parseLogical()); return assignNode;
    }

    private ASTNode parseAssignment() { ASTNode node = parseAssignmentInner(); expectText(";"); return node; }

    private ASTNode parseFuncCall(Token idToken) {
        ASTNode callNode = new ASTNode("FuncCall"); callNode.setValue(idToken.getText());
        expectText("("); 
        while (current() != null && !current().getText().equals(")")) {
            if (current().getText().startsWith("'") || current().getText().startsWith("\"")) {
                ASTNode strNode = new ASTNode("String"); strNode.setValue(current().getText()); callNode.addChild(strNode); pos++;
            } else callNode.addChild(parseLogical()); 
            if (matchText(",") == null) break;
        }
        expectText(")"); return callNode;
    }

    private ASTNode parseCompoundStmt() { ASTNode compound = new ASTNode("Compound"); expectText("{"); while (current() != null && !current().getText().equals("}")) { ASTNode stmt = parseStatement(); if (stmt != null) compound.addChild(stmt); else pos++; } expectText("}"); return compound; }
    private ASTNode parseIfStmt() { ASTNode ifNode = new ASTNode("IfStmt"); expectText("if"); expectText("("); ifNode.addChild(parseLogical()); expectText(")"); ifNode.addChild(parseStatement()); if (matchText("else") != null) ifNode.addChild(parseStatement()); return ifNode; }
    private ASTNode parseWhileStmt() { ASTNode whileNode = new ASTNode("WhileStmt"); expectText("while"); expectText("("); whileNode.addChild(parseLogical()); expectText(")"); whileNode.addChild(parseStatement()); return whileNode; }
    private ASTNode parseLogical() { ASTNode left = parseRelational(); if (left == null) return null; Token curr = current(); while (curr != null && (curr.getText().equals("&&") || curr.getText().equals("||"))) { pos++; ASTNode opNode = new ASTNode("BinOp"); opNode.setValue(curr.getText()); ASTNode right = parseRelational(); opNode.addChild(left); opNode.addChild(right); left = opNode; curr = current(); } return left; }
    private ASTNode parseRelational() { ASTNode left = parseExpression(); if (left == null) return null; Token curr = current(); while (curr != null && (curr.getText().equals(">") || curr.getText().equals("<") || curr.getText().equals(">=") || curr.getText().equals("<=") || curr.getText().equals("==") || curr.getText().equals("!="))) { pos++; ASTNode opNode = new ASTNode("RelOp"); opNode.setValue(curr.getText()); ASTNode right = parseExpression(); opNode.addChild(left); opNode.addChild(right); left = opNode; curr = current(); } return left; }
    private ASTNode parseExpression() { ASTNode left = parseTerm(); if (left == null) return null; Token curr = current(); while (curr != null && (curr.getText().equals("+") || curr.getText().equals("-"))) { pos++; ASTNode opNode = new ASTNode("BinOp"); opNode.setValue(curr.getText()); ASTNode right = parseTerm(); opNode.addChild(left); opNode.addChild(right); left = opNode; curr = current(); } return left; }
    private ASTNode parseTerm() { ASTNode left = parseFactor(); if (left == null) return null; Token curr = current(); while (curr != null && (curr.getText().equals("*") || curr.getText().equals("/") || curr.getText().equals("%"))) { pos++; ASTNode opNode = new ASTNode("BinOp"); opNode.setValue(curr.getText()); ASTNode right = parseFactor(); opNode.addChild(left); opNode.addChild(right); left = opNode; curr = current(); } return left; }

    private ASTNode parseFactor() {
        Token curr = current(); if (curr == null) return null;
        if (curr.getText().equals("-")) { pos++; ASTNode unaryNode = new ASTNode("UnaryOp"); unaryNode.setValue("-"); unaryNode.addChild(parseFactor()); return unaryNode; }
        if (curr.getKind().equals("int_literal") || curr.getKind().equals("float_literal")) { ASTNode node = new ASTNode("Literal"); node.setValue(curr.getText()); pos++; return node; } 
        else if (curr.getKind().equals("identifier") || curr.getText().equals("read")) {
            if (pos + 1 < tokens.size() && tokens.get(pos + 1).getText().equals("(")) { Token idToken = current(); pos++; return parseFuncCall(idToken); }
            // 终极升级：解析数组求值 a[i]
            if (pos + 1 < tokens.size() && tokens.get(pos + 1).getText().equals("[")) {
                Token idToken = current(); pos++; expectText("[");
                ASTNode arrayAccess = new ASTNode("ArrayAccess"); arrayAccess.setValue(idToken.getText());
                arrayAccess.addChild(parseLogical()); expectText("]"); return arrayAccess;
            }
            ASTNode node = new ASTNode("Identifier"); node.setValue(curr.getText()); pos++; return node;
        } else if (matchText("(") != null) { ASTNode expr = parseLogical(); expectText(")"); return expr; }
        return null;
    }
}