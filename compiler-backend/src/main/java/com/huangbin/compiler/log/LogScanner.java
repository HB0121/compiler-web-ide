package com.huangbin.compiler.log;

import com.huangbin.compiler.regex.*;
import java.util.*;

/**
 * 日志扫描器 — 正则 → NFA → DFA → 日志扫描
 * 用户输入日志文本和正则表达式，生成 NFA 和 DFA 并用 DFA 扫描匹配行
 *
 * @author 黄彬 (12303070250)
 */
public class LogScanner {

    private final String logText;
    private final String regex;
    private RegexParser.Node astRoot;
    private NFABuilder.NFA nfa;
    private DFABuilder.DFA dfa;
    private String nfaText;
    private String dfaText;
    private String error;

    public LogScanner(String logText, String regex) {
        this.logText = logText != null ? logText : "";
        this.regex = regex != null ? regex.trim() : "";
    }

    public boolean execute() {
        if (regex.isEmpty()) {
            error = "正则表达式为空";
            return false;
        }

        // 1. 解析正则表达式
        try {
            RegexParser parser = new RegexParser(regex);
            astRoot = parser.parse();
        } catch (Exception e) {
            error = "正则解析错误: " + e.getMessage();
            return false;
        }

        // 2. 生成 NFA
        try {
            NFABuilder builder = new NFABuilder();
            nfa = builder.build(astRoot);
            nfaText = formatNFA(nfa);
        } catch (Exception e) {
            error = "NFA 构造错误: " + e.getMessage();
            return false;
        }

        // 3. 转换为 DFA
        try {
            DFABuilder builder = new DFABuilder(nfa);
            dfa = builder.build();
            dfaText = dfa.toString();
        } catch (Exception e) {
            error = "DFA 构造错误: " + e.getMessage();
            return false;
        }

        return true;
    }

    /** 用 DFA 扫描日志，返回匹配的行 */
    public List<ScanResult> scan() {
        List<ScanResult> results = new ArrayList<>();
        if (dfa == null || logText.isEmpty()) return results;

        String[] lines = logText.split("\\R");
        for (int lineNo = 0; lineNo < lines.length; lineNo++) {
            String line = lines[lineNo];
            List<Match> matches = scanLine(line, lineNo + 1);
            if (!matches.isEmpty()) {
                results.add(new ScanResult(lineNo + 1, line, matches));
            }
        }
        return results;
    }

    /** 扫描单行，找出所有匹配 */
    private List<Match> scanLine(String line, int lineNo) {
        List<Match> matches = new ArrayList<>();
        int n = line.length();

        for (int start = 0; start < n; start++) {
            int currentState = dfa.startState;
            int longestEnd = -1;

            for (int i = start; i < n; i++) {
                char ch = line.charAt(i);
                Map<Character, Integer> trans = dfa.transitions.get(currentState);
                if (trans == null) break;
                Integer next = trans.get(ch);
                if (next == null) break;
                currentState = next;
                if (dfa.acceptStates.contains(currentState)) {
                    longestEnd = i;
                }
            }

            if (longestEnd >= start) {
                String matched = line.substring(start, longestEnd + 1);
                // 跳过空匹配
                if (!matched.isEmpty()) {
                    matches.add(new Match(start, longestEnd, matched));
                    start = longestEnd; // 跳过已匹配部分
                }
            }
        }
        return matches;
    }

    // ==================== NFA 格式化输出 ====================

    private String formatNFA(NFABuilder.NFA nfa) {
        StringBuilder sb = new StringBuilder();
        sb.append("NFA 状态数: ").append(nfa.totalStates).append("\n");
        sb.append("起始状态: S").append(nfa.startState).append("\n");
        sb.append("接受状态: S").append(nfa.acceptState).append("\n");

        // 收集所有边
        List<String> edges = new ArrayList<>();

        // 字符转移
        for (Map.Entry<Integer, Map<Character, Set<Integer>>> e : nfa.transitions.entrySet()) {
            int from = e.getKey();
            for (Map.Entry<Character, Set<Integer>> e2 : e.getValue().entrySet()) {
                for (int to : e2.getValue()) {
                    edges.add(String.format("  S%d -- [%s] --> S%d", from,
                        e2.getKey() == '\n' ? "\\n" : e2.getKey() == '\r' ? "\\r" : e2.getKey(), to));
                }
            }
        }

        // ε 转移
        for (Map.Entry<Integer, Set<Integer>> e : nfa.epsilonTransitions.entrySet()) {
            int from = e.getKey();
            for (int to : e.getValue()) {
                edges.add(String.format("  S%d -- [ε] --> S%d", from, to));
            }
        }

        if (!edges.isEmpty()) {
            sb.append("\n转移边:\n");
            for (String edge : edges) {
                sb.append(edge).append("\n");
            }
        }

        return sb.toString();
    }

    // ==================== Getters ====================

    public NFABuilder.NFA getNFA() { return nfa; }
    public DFABuilder.DFA getDFA() { return dfa; }
    public String getNFAText() { return nfaText; }
    public String getDFAText() { return dfaText; }
    public String getError() { return error; }
    public String getASTString() { return astRoot != null ? astRoot.toString() : "null"; }

    // ==================== 数据类 ====================

    public static class Match {
        public final int startCol;   // 0-indexed
        public final int endCol;     // inclusive
        public final String text;

        Match(int startCol, int endCol, String text) {
            this.startCol = startCol; this.endCol = endCol; this.text = text;
        }
    }

    public static class ScanResult {
        public final int lineNo;
        public final String content;
        public final List<Match> matches;

        ScanResult(int lineNo, String content, List<Match> matches) {
            this.lineNo = lineNo; this.content = content; this.matches = matches;
        }
    }
}
