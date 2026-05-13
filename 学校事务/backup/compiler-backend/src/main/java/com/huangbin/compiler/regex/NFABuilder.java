package com.huangbin.compiler.regex;

import java.util.*;

/**
 * Thompson 构造法 —— 正则 AST → NFA
 *
 * @author 黄彬 (12303070250)
 */
public class NFABuilder {

    /** NFA 定义 */
    public static class NFA {
        public int startState;
        public int acceptState;
        public final Map<Integer, Map<Character, Set<Integer>>> transitions = new LinkedHashMap<>();
        public final Map<Integer, Set<Integer>> epsilonTransitions = new LinkedHashMap<>();
        public final int totalStates;

        NFA(int startState, int acceptState, int totalStates) {
            this.startState = startState;
            this.acceptState = acceptState;
            this.totalStates = totalStates;
        }

        void addTransition(int from, char ch, int to) {
            transitions.computeIfAbsent(from, k -> new LinkedHashMap<>())
                        .computeIfAbsent(ch, k -> new LinkedHashSet<>()).add(to);
        }

        void addEpsilon(int from, int to) {
            epsilonTransitions.computeIfAbsent(from, k -> new LinkedHashSet<>()).add(to);
        }

        /** 合并另一个 NFA 的转换到此 NFA */
        void merge(NFA other) {
            for (Map.Entry<Integer, Map<Character, Set<Integer>>> e : other.transitions.entrySet()) {
                for (Map.Entry<Character, Set<Integer>> e2 : e.getValue().entrySet()) {
                    for (int to : e2.getValue()) {
                        addTransition(e.getKey(), e2.getKey(), to);
                    }
                }
            }
            for (Map.Entry<Integer, Set<Integer>> e : other.epsilonTransitions.entrySet()) {
                for (int to : e.getValue()) {
                    addEpsilon(e.getKey(), to);
                }
            }
        }
    }

    private int stateCounter = 0;

    private int newState() { return stateCounter++; }

    public NFA build(RegexParser.Node root) {
        stateCounter = 0;
        return buildNode(root);
    }

    private NFA buildNode(RegexParser.Node node) {
        if (node instanceof RegexParser.CharNode) {
            return buildChar(((RegexParser.CharNode) node).ch);
        } else if (node instanceof RegexParser.ConcatNode) {
            RegexParser.ConcatNode cn = (RegexParser.ConcatNode) node;
            return buildConcat(buildNode(cn.left), buildNode(cn.right));
        } else if (node instanceof RegexParser.UnionNode) {
            RegexParser.UnionNode un = (RegexParser.UnionNode) node;
            return buildUnion(buildNode(un.left), buildNode(un.right));
        } else if (node instanceof RegexParser.StarNode) {
            return buildStar(buildNode(((RegexParser.StarNode) node).child));
        }
        throw new IllegalArgumentException("未知 AST 节点");
    }

    /** 单字符 NFA: start --ch--> accept */
    private NFA buildChar(char ch) {
        int s = newState();
        int a = newState();
        NFA nfa = new NFA(s, a, 2);
        if (ch != 0) nfa.addTransition(s, ch, a); // ch==0 means epsilon
        else nfa.addEpsilon(s, a);
        return nfa;
    }

    /** 连接: A 的 accept 用 ε 连到 B 的 start */
    private NFA buildConcat(NFA a, NFA b) {
        NFA nfa = new NFA(a.startState, b.acceptState, 0);
        nfa.merge(a);
        nfa.merge(b);
        nfa.addEpsilon(a.acceptState, b.startState);
        return nfa;
    }

    /** 并: 新 start -ε→ A.start, B.start; A.accept -ε→ 新accept; B.accept -ε→ 新accept */
    private NFA buildUnion(NFA a, NFA b) {
        int s = newState();
        int acc = newState();
        NFA nfa = new NFA(s, acc, 0);
        nfa.merge(a);
        nfa.merge(b);
        nfa.addEpsilon(s, a.startState);
        nfa.addEpsilon(s, b.startState);
        nfa.addEpsilon(a.acceptState, acc);
        nfa.addEpsilon(b.acceptState, acc);
        return nfa;
    }

    /** 闭包: 新start -ε→ A.start, 新start -ε→ 新accept; A.accept -ε→ A.start; A.accept -ε→ 新accept */
    private NFA buildStar(NFA a) {
        int s = newState();
        int acc = newState();
        NFA nfa = new NFA(s, acc, 0);
        nfa.merge(a);
        nfa.addEpsilon(s, a.startState);
        nfa.addEpsilon(s, acc);
        nfa.addEpsilon(a.acceptState, a.startState);
        nfa.addEpsilon(a.acceptState, acc);
        return nfa;
    }
}
