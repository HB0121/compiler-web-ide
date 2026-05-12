package com.huangbin.compiler.lexer;

import com.huangbin.compiler.model.Diagnostic;
import com.huangbin.compiler.model.Token;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Lexer {

    // 测试用代码，跑通后可以删掉
    public static void main(String[] args) {
        String testCode = "int main() { \n // 测试注释 \n int x = 10; \n return x; \n }";
        Lexer lexer = new Lexer();
        LexerResult result = lexer.tokenize(testCode);

        System.out.println("====== Tokens ======");
        result.tokens.forEach(System.out::println);

        System.out.println("====== Errors ======");
        result.diagnostics.forEach(d -> System.out.println(d.format()));
    }

    private static final Map<String, Integer> KEYWORDS = new HashMap<>();
    private static final Map<String, Integer> OPERATORS = new HashMap<>();
    private static final Map<String, Character> SEPARATORS = new HashMap<>();

    public static final int IDENTIFIER_CODE = 700;
    public static final int INT_LITERAL_CODE = 401;
    public static final int FLOAT_LITERAL_CODE = 402;
    public static final int CHAR_LITERAL_CODE = 403;

    static {
        // 初始化关键字
        String[] keywords = {"const", "int", "float", "char", "void", "return", "if", "else", "while", "do", "for", "break", "continue"};
        int kwCode = 100;
        for (String kw : keywords) KEYWORDS.put(kw, kwCode++);

        // 初始化运算符
        OPERATORS.put("==", 201); OPERATORS.put("!=", 202);
        OPERATORS.put("<=", 203); OPERATORS.put(">=", 204);
        OPERATORS.put("&&", 205); OPERATORS.put("||", 206);
        OPERATORS.put("=", 207);  OPERATORS.put(">", 208);
        OPERATORS.put("<", 209);  OPERATORS.put("+", 210);
        OPERATORS.put("-", 211);  OPERATORS.put("*", 212);
        OPERATORS.put("/", 213);  OPERATORS.put("!", 214);

        // 初始化分隔符
        SEPARATORS.put(";", '1'); SEPARATORS.put(",", '2');
        SEPARATORS.put("(", '3'); SEPARATORS.put(")", '4');
        SEPARATORS.put("{", '5'); SEPARATORS.put("}", '6');
    }

    // 用于封装返回结果的内部类
    public static class LexerResult {
        public List<Token> tokens = new ArrayList<>();
        public List<Diagnostic> diagnostics = new ArrayList<>();
    }

    public LexerResult tokenize(String source) {
        LexerResult result = new LexerResult();
        int i = 0, line = 1, column = 1;
        int length = source.length();

        while (i < length) {
            char ch = source.charAt(i);

            // 1. 跳过空白字符
            if (ch == ' ' || ch == '\t' || ch == '\r') {
                i++; column++; continue;
            }
            if (ch == '\n') {
                i++; line++; column = 1; continue;
            }

            // 2. 处理单行注释 //
            if (source.startsWith("//", i)) {
                while (i < length && source.charAt(i) != '\n') {
                    i++; column++;
                }
                continue;
            }

            // 3. 处理多行注释 /* ... */
            if (source.startsWith("/*", i)) {
                int startLine = line, startColumn = column;
                i += 2; column += 2;
                boolean closed = false;
                while (i < length) {
                    if (source.startsWith("*/", i)) {
                        i += 2; column += 2;
                        closed = true; break;
                    }
                    if (source.charAt(i) == '\n') {
                        i++; line++; column = 1;
                    } else {
                        i++; column++;
                    }
                }
                if (!closed) {
                    result.diagnostics.add(new Diagnostic("lexer", startLine, "L001", "unclosed comment at column " + startColumn));
                }
                continue;
            }

            // 4. 处理标识符和关键字
            if (Character.isLetter(ch) || ch == '_') {
                int start = i, startColumn = column;
                while (i < length && (Character.isLetterOrDigit(source.charAt(i)) || source.charAt(i) == '_')) {
                    i++; column++;
                }
                String text = source.substring(start, i);
                if (KEYWORDS.containsKey(text)) {
                    result.tokens.add(new Token(text, KEYWORDS.get(text), line, startColumn, "keyword"));
                } else {
                    result.tokens.add(new Token(text, IDENTIFIER_CODE, line, startColumn, "identifier"));
                }
                continue;
            }

            // 5. 处理数字字面量 (整数和浮点数)
            if (Character.isDigit(ch)) {
                int start = i, startColumn = column;
                boolean hasDot = false;
                while (i < length && (Character.isDigit(source.charAt(i)) || source.charAt(i) == '.')) {
                    if (source.charAt(i) == '.') {
                        if (hasDot) break; // 出现第二个小数点则停止
                        hasDot = true;
                    }
                    i++; column++;
                }
                String text = source.substring(start, i);
                int code = hasDot ? FLOAT_LITERAL_CODE : INT_LITERAL_CODE;
                String kind = hasDot ? "float_literal" : "int_literal";
                result.tokens.add(new Token(text, code, line, startColumn, kind));
                continue;
            }

            // 6. 处理字符字面量 'a'
            if (ch == '\'') {
                int start = i, startColumn = column;
                i++; column++;
                while (i < length && source.charAt(i) != '\'' && source.charAt(i) != '\n') {
                    i++; column++;
                }
                if (i < length && source.charAt(i) == '\'') {
                    i++; column++;
                    result.tokens.add(new Token(source.substring(start, i), CHAR_LITERAL_CODE, line, startColumn, "char_literal"));
                } else {
                    result.diagnostics.add(new Diagnostic("lexer", line, "L002", "unclosed char literal at column " + startColumn));
                }
                continue;
            }

            // 7. 处理双字符运算符 (如 ==, <=)
            if (i + 1 < length) {
                String twoChars = source.substring(i, i + 2);
                if (OPERATORS.containsKey(twoChars)) {
                    result.tokens.add(new Token(twoChars, OPERATORS.get(twoChars), line, column, "operator"));
                    i += 2; column += 2;
                    continue;
                }
            }

            // 8. 处理单字符运算符
            if (OPERATORS.containsKey(String.valueOf(ch))) {
                result.tokens.add(new Token(String.valueOf(ch), OPERATORS.get(String.valueOf(ch)), line, column, "operator"));
                i++; column++;
                continue;
            }

            // 9. 处理分隔符
            if (SEPARATORS.containsKey(String.valueOf(ch))) {
                // 借用分隔符的值计算 code，这里为了简单直接给 300+ 分隔符映射
                int sepCode = 300 + Integer.parseInt(SEPARATORS.get(String.valueOf(ch)).toString());
                result.tokens.add(new Token(String.valueOf(ch), sepCode, line, column, "separator"));
                i++; column++;
                continue;
            }

            // 10. 未知字符处理
            result.diagnostics.add(new Diagnostic("lexer", line, "L003", "unknown character '" + ch + "' at column " + column));
            i++; column++;
        }

        return result;
    }
}