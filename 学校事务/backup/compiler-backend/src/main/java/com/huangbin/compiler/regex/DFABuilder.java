package com.huangbin.compiler.regex;

import java.util.*;

/**
 * 子集构造法 —— NFA → DFA
 *
 * @author 黄彬 (12303070250)
 */
public class DFABuilder {

    /** DFA 定义 */
    public static class DFA {
        /** DFA 状态 id → 对应的 NFA 状态集合 */
        public final Map<Integer, Set<Integer>> stateLabel = new LinkedHashMap<>();
        /** 转移表: state × char → nextState */
        public final Map<Integer, Map<Character, Integer>> transitions = new LinkedHashMap<>();
        public int startState;
        public final Set<Integer> acceptStates = new LinkedHashSet<>();
        public final Set<Character> alphabet = new LinkedHashSet<>();
        public int stateCount;

        @Override
        public String toString() {
            StringBuilder sb = new StringBuilder();
            sb.append("DFA 状态数: ").append(stateCount).append("\n");
            sb.append("字母表: ").append(alphabet).append("\n");
            sb.append("起始状态: ").append(startState).append("\n");
            sb.append("接受状态: ").append(acceptStates).append("\n\n");
            sb.append("状态转移表:\n");
            List<Character> sortedAlpha = new ArrayList<>(alphabet);
            Collections.sort(sortedAlpha);
            sb.append(String.format("  %-6s", "状态"));
            for (char c : sortedAlpha) sb.append(String.format("%-8s", c));
            sb.append("  标记\n");
            sb.append("  ").append("-".repeat(60)).append("\n");
            for (int i = 0; i < stateCount; i++) {
                String mark = acceptStates.contains(i) ? "接受" : (i == startState ? "起始" : "");
                sb.append(String.format("  S%-4d", i));
                for (char c : sortedAlpha) {
                    Integer next = transitions.getOrDefault(i, Collections.emptyMap()).get(c);
                    sb.append(String.format("%-8s", next != null ? "S" + next : "-"));
                }
                sb.append("  ").append(mark).append("\n");
            }
            return sb.toString();
        }
    }

    private final NFABuilder.NFA nfa;
    private final DFA dfa = new DFA();

    public DFABuilder(NFABuilder.NFA nfa) {
        this.nfa = nfa;
    }

    public DFA build() {
        // 收集字母表
        for (Map<Character, Set<Integer>> map : nfa.transitions.values()) {
            dfa.alphabet.addAll(map.keySet());
        }

        // 起始: ε-closure(nfa.startState)
        Set<Integer> startSet = epsilonClosure(Set.of(nfa.startState));
        Map<Set<Integer>, Integer> setToState = new LinkedHashMap<>();
        Queue<Set<Integer>> workList = new LinkedList<>();

        setToState.put(startSet, dfa.stateCount);
        dfa.stateLabel.put(dfa.stateCount, startSet);
        if (startSet.contains(nfa.acceptState)) dfa.acceptStates.add(dfa.stateCount);
        dfa.startState = dfa.stateCount;
        dfa.stateCount++;
        workList.add(startSet);

        while (!workList.isEmpty()) {
            Set<Integer> current = workList.poll();
            int currentId = setToState.get(current);

            for (char ch : dfa.alphabet) {
                Set<Integer> nextSet = epsilonClosure(move(current, ch));
                if (nextSet.isEmpty()) continue;

                Integer nextId = setToState.get(nextSet);
                if (nextId == null) {
                    nextId = dfa.stateCount;
                    setToState.put(nextSet, nextId);
                    dfa.stateLabel.put(nextId, nextSet);
                    if (nextSet.contains(nfa.acceptState)) dfa.acceptStates.add(nextId);
                    dfa.stateCount++;
                    workList.add(nextSet);
                }

                dfa.transitions.computeIfAbsent(currentId, k -> new LinkedHashMap<>()).put(ch, nextId);
            }
        }

        return dfa;
    }

    /** ε-闭包 */
    private Set<Integer> epsilonClosure(Set<Integer> states) {
        Set<Integer> closure = new LinkedHashSet<>(states);
        Stack<Integer> stack = new Stack<>();
        stack.addAll(states);

        while (!stack.isEmpty()) {
            int s = stack.pop();
            Set<Integer> epsTargets = nfa.epsilonTransitions.get(s);
            if (epsTargets != null) {
                for (int t : epsTargets) {
                    if (closure.add(t)) stack.push(t);
                }
            }
        }
        return closure;
    }

    /** move(T, ch): 从状态集 T 出发，经过字符 ch 可达的状态集 */
    private Set<Integer> move(Set<Integer> states, char ch) {
        Set<Integer> result = new LinkedHashSet<>();
        for (int s : states) {
            Map<Character, Set<Integer>> trans = nfa.transitions.get(s);
            if (trans != null) {
                Set<Integer> targets = trans.get(ch);
                if (targets != null) result.addAll(targets);
            }
        }
        return result;
    }
}
