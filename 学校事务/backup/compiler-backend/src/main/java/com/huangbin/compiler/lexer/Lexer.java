package com.huangbin.compiler.lexer;

import com.huangbin.compiler.model.Diagnostic;
import com.huangbin.compiler.model.Token;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Lexer {
    private final String sourceCode;
    private int pos = 0;
    private int line = 1;
    private int column = 1;

    private final List<Token> tokens = new ArrayList<>();
    private final List<Diagnostic> diagnostics = new ArrayList<>();

    // 预定义词法字典
    private static final Map<String, Integer> KEYWORDS = new HashMap<>();
    private static final Map<String, Integer> OPERATORS = new HashMap<>();

    static {
        // 初始化关键字
        KEYWORDS.put("int", 101); KEYWORDS.put("float", 102); KEYWORDS.put("char", 103);
        KEYWORDS.put("void", 104); KEYWORDS.put("main", 105); KEYWORDS.put("if", 106);
        KEYWORDS.put("else", 107); KEYWORDS.put("while", 108); KEYWORDS.put("for", 109);
        KEYWORDS.put("read", 110); KEYWORDS.put("write", 111); KEYWORDS.put("const", 112);
        KEYWORDS.put("return", 113); KEYWORDS.put("break", 114); KEYWORDS.put("continue", 115);

        // 初始化双字符和单字符操作符
        OPERATORS.put("==", 201); OPERATORS.put("!=", 202); OPERATORS.put("<=", 203);
        OPERATORS.put(">=", 204); OPERATORS.put("&&", 205); OPERATORS.put("||", 206);
        OPERATORS.put("=", 207);  OPERATORS.put(">", 208);  OPERATORS.put("<", 209);
        OPERATORS.put("+", 210);  OPERATORS.put("-", 211);  OPERATORS.put("*", 212);
        OPERATORS.put("/", 213);  OPERATORS.put("%", 214);  OPERATORS.put("!", 215);

        // 初始化界符
        OPERATORS.put("(", 301); OPERATORS.put(")", 302); OPERATORS.put("{", 303);
        OPERATORS.put("}", 304); OPERATORS.put("[", 305); OPERATORS.put("]", 306);
        OPERATORS.put(";", 307); OPERATORS.put(",", 308);
    }

    public Lexer(String sourceCode) {
        this.sourceCode = sourceCode == null ? "" : sourceCode;
    }

    public List<Token> getTokens() { return tokens; }
    public List<Diagnostic> getDiagnostics() { return diagnostics; }

    // 辅助获取字符
    private char current() { return pos < sourceCode.length() ? sourceCode.charAt(pos) : '\0'; }
    private char peek() { return pos + 1 < sourceCode.length() ? sourceCode.charAt(pos + 1) : '\0'; }

    // 游标前进并维护行号列号
    private void advance() {
        if (current() == '\n') { line++; column = 1; }
        else { column++; }
        pos++;
    }

    // 【兼容性设置】：创建 Token 的工厂方法
    private void createToken(int startLine, int startCol, String text, String kind, int code) {
        /*
         * 注意：如果你的 Token 类是通过 new Token(line, col, text, kind, code) 实例化的，
         * 请将下面的代码替换为：tokens.add(new Token(startLine, startCol, text, kind, code));
         */
        Token t = new Token();
        t.setLine(startLine);
        t.setColumn(startCol);
        t.setText(text);
        t.setKind(kind);
        t.setCode(code);
        tokens.add(t);
    }

    public void tokenize() {
        while (pos < sourceCode.length()) {
            char ch = current();

            // 1. 跳过空白字符
            if (Character.isWhitespace(ch)) { advance(); continue; }

            // 2. 跳过单行注释 //
            if (ch == '/' && peek() == '/') {
                while (current() != '\n' && current() != '\0') advance();
                continue;
            }

            // 3. 跳过多行注释 /* */
            if (ch == '/' && peek() == '*') {
                advance(); advance();
                while (current() != '\0' && !(current() == '*' && peek() == '/')) advance();
                if (current() != '\0') { advance(); advance(); }
                continue;
            }

            // 4. 【核心修复】：精准拦截单引号和双引号包裹的字符串！
            if (ch == '"' || ch == '\'') {
                char quote = ch;
                int startCol = column;
                StringBuilder str = new StringBuilder();
                str.append(ch); // 存入开头引号
                advance();

                while (current() != '\0' && current() != quote) {
                    str.append(current());
                    advance();
                }

                if (current() == quote) {
                    str.append(current()); // 存入结尾引号
                    advance();
                } else {
                    diagnostics.add(new Diagnostic("lexer", line, "L001", "字符串缺少闭合引号"));
                }

                createToken(line, startCol, str.toString(), "string_literal", 800);
                continue;
            }

            // 5. 识别关键字和标识符
            if (Character.isLetter(ch) || ch == '_') {
                int startCol = column;
                StringBuilder sb = new StringBuilder();
                while (Character.isLetterOrDigit(current()) || current() == '_') {
                    sb.append(current());
                    advance();
                }
                String text = sb.toString();
                if (KEYWORDS.containsKey(text)) {
                    createToken(line, startCol, text, "keyword", KEYWORDS.get(text));
                } else {
                    createToken(line, startCol, text, "identifier", 400);
                }
                continue;
            }

            // 6. 识别数字 (支持小数)
            if (Character.isDigit(ch)) {
                int startCol = column;
                StringBuilder sb = new StringBuilder();
                boolean hasDot = false;
                while (Character.isDigit(current()) || current() == '.') {
                    if (current() == '.') {
                        if (hasDot) break; // 防止 1.2.3 这种非法数字
                        hasDot = true;
                    }
                    sb.append(current());
                    advance();
                }
                createToken(line, startCol, sb.toString(), hasDot ? "float_literal" : "int_literal", hasDot ? 501 : 500);
                continue;
            }

            // 7. 识别双字符操作符 (如 ==, <=, &&)
            String twoCharOp = "" + ch + peek();
            if (OPERATORS.containsKey(twoCharOp)) {
                createToken(line, column, twoCharOp, "operator", OPERATORS.get(twoCharOp));
                advance(); advance();
                continue;
            }

            // 8. 识别单字符操作符和界符 (如 +, =, ;)
            String oneCharOp = "" + ch;
            if (OPERATORS.containsKey(oneCharOp)) {
                createToken(line, column, oneCharOp, "operator", OPERATORS.get(oneCharOp));
                advance();
                continue;
            }

            // 9. 容错处理：未知字符报错并跳过
            diagnostics.add(new Diagnostic("lexer", line, "L003", "unknown character '" + ch + "' at column " + column));
            advance();
        }
    }
}