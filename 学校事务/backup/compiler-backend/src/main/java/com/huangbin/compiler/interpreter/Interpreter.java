package com.huangbin.compiler.interpreter;

import com.huangbin.compiler.ir.IRGenerator.Quad;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Interpreter {

    private final List<Quad> quads;
    private final Map<String, Integer> memory = new HashMap<>();
    private final List<String> outputLogs = new ArrayList<>();

    public Interpreter(List<Quad> quads) { this.quads = quads; }

    private int getValue(String arg) {
        if (arg == null || arg.equals("_")) return 0;
        try { return Integer.parseInt(arg); }
        catch (NumberFormatException e) { return memory.getOrDefault(arg, 0); }
    }

    public List<String> run() {
        outputLogs.add("🚀 开始解释执行...");
        int maxSteps = 1000; // 防止死循环的安全机制
        int steps = 0;

        // 注意：这里的 i 不在 for 括号里自增了，由内部指令控制！
        for (int i = 0; i < quads.size() && steps < maxSteps; steps++) {
            Quad q = quads.get(i);
            int nextI = i + 1; // 默认下一条指令是 i+1

            switch (q.op) {
                case "=":
                    memory.put(q.result, getValue(q.arg1));
                    outputLogs.add(String.format("[%d] 👉 赋值: %s = %d", i, q.result, getValue(q.arg1)));
                    break;
                case "+":
                case "-":
                case "*":
                case "/":
                    int v1 = getValue(q.arg1), v2 = getValue(q.arg2), res = 0;
                    if (q.op.equals("+")) res = v1 + v2;
                    else if (q.op.equals("-")) res = v1 - v2;
                    else if (q.op.equals("*")) res = v1 * v2;
                    else if (q.op.equals("/")) res = v2 != 0 ? v1 / v2 : 0;
                    memory.put(q.result, res);
                    outputLogs.add(String.format("[%d] 🧮 计算: %s = %d %s %d = %d", i, q.result, v1, q.op, v2, res));
                    break;

                // ================= 跳转指令处理 =================
                case "J":
                    nextI = Integer.parseInt(q.result);
                    outputLogs.add(String.format("[%d] 🔀 无条件跳转至 -> %d", i, nextI));
                    break;
                case "J<":
                    if (getValue(q.arg1) < getValue(q.arg2)) {
                        nextI = Integer.parseInt(q.result);
                        outputLogs.add(String.format("[%d] ✔️ 条件成立 (%d < %d), 跳转至 -> %d", i, getValue(q.arg1), getValue(q.arg2), nextI));
                    } else {
                        outputLogs.add(String.format("[%d] ❌ 条件不成立 (%d < %d), 继续往下执行", i, getValue(q.arg1), getValue(q.arg2)));
                    }
                    break;
                case "J>":
                    if (getValue(q.arg1) > getValue(q.arg2)) {
                        nextI = Integer.parseInt(q.result);
                        outputLogs.add(String.format("[%d] ✔️ 条件成立 (%d > %d), 跳转至 -> %d", i, getValue(q.arg1), getValue(q.arg2), nextI));
                    }
                    break;
                case "J==":
                    if (getValue(q.arg1) == getValue(q.arg2)) {
                        nextI = Integer.parseInt(q.result);
                        outputLogs.add(String.format("[%d] ✔️ 条件成立 (%d == %d), 跳转至 -> %d", i, getValue(q.arg1), getValue(q.arg2), nextI));
                    }
                    break;
            }
            i = nextI; // 更新程序计数器
        }

        if (steps >= maxSteps) outputLogs.add("⚠️ 触发安全限制：代码疑似出现死循环，已被强行中止！");
        outputLogs.add("✅ 执行完毕！最终内存状态: " + memory.toString());
        return outputLogs;
    }
}