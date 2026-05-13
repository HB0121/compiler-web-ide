package com.huangbin.compiler.regex;

import java.util.*;

/**
 * 正则表达式解析器 — 将正则字符串解析为 AST
 * 支持: 字面字符、连接、|、*、()、转义 \* \| \( \) \\
 *
 * @author 黄彬 (12303070250)
 */
public class RegexParser {

    public abstract static class Node {
        @Override public abstract String toString();
    }
    public static class CharNode extends Node {
        public char ch;
        public CharNode(char ch) { this.ch = ch; }
        @Override public String toString() { return ch == 0 ? "ε" : String.valueOf(ch); }
    }
    public static class ConcatNode extends Node {
        public Node left, right;
        public ConcatNode(Node left, Node right) { this.left = left; this.right = right; }
        @Override public String toString() { return "(" + left + right + ")"; }
    }
    public static class UnionNode extends Node {
        public Node left, right;
        public UnionNode(Node left, Node right) { this.left = left; this.right = right; }
        @Override public String toString() { return "(" + left + "|" + right + ")"; }
    }
    public static class StarNode extends Node {
        public Node child;
        public StarNode(Node child) { this.child = child; }
        @Override public String toString() { return child + "*"; }
    }

    private final String regex;
    private int pos;

    public RegexParser(String regex) {
        this.regex = regex;
        this.pos = 0;
    }

    public Node parse() {
        Node result = parseUnion();
        if (pos < regex.length()) {
            throw new IllegalArgumentException("多余的字符 '" + regex.charAt(pos) + "' 位于位置 " + pos);
        }
        return result;
    }

    /** 最低优先级: | */
    private Node parseUnion() {
        Node left = parseConcat();
        while (pos < regex.length() && regex.charAt(pos) == '|') {
            pos++; // skip |
            Node right = parseConcat();
            left = new UnionNode(left, right);
        }
        return left;
    }

    /** 连接 */
    private Node parseConcat() {
        List<Node> parts = new ArrayList<>();
        while (pos < regex.length() && regex.charAt(pos) != '|' && regex.charAt(pos) != ')') {
            parts.add(parseStar());
        }
        if (parts.isEmpty()) return new CharNode((char) 0); // ε
        if (parts.size() == 1) return parts.get(0);
        Node result = parts.get(0);
        for (int i = 1; i < parts.size(); i++) {
            result = new ConcatNode(result, parts.get(i));
        }
        return result;
    }

    /** * 闭包 */
    private Node parseStar() {
        Node node = parseAtom();
        while (pos < regex.length() && regex.charAt(pos) == '*') {
            pos++;
            node = new StarNode(node);
        }
        return node;
    }

    /** 原子: 字符 或 (...) */
    private Node parseAtom() {
        if (pos >= regex.length()) return new CharNode((char) 0);

        char ch = regex.charAt(pos);

        if (ch == '(') {
            pos++;
            Node node = parseUnion();
            if (pos < regex.length() && regex.charAt(pos) == ')') {
                pos++;
            } else {
                throw new IllegalArgumentException("缺少右括号 ')' 位于位置 " + pos);
            }
            return node;
        }

        if (ch == '\\') {
            pos++;
            if (pos >= regex.length()) throw new IllegalArgumentException("转义符 \\ 后缺少字符");
            char escaped = regex.charAt(pos);
            pos++;
            return new CharNode(escaped);
        }

        // 普通字符
        pos++;
        return new CharNode(ch);
    }
}
