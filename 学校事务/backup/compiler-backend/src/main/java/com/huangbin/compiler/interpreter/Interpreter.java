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
        int maxSteps = 1000;
        int steps = 0;

        for (int i = 0; i < quads.size() && steps < maxSteps; steps++) {
            Quad q = quads.get(i);
            int nextI = i + 1;

            switch (q.op) {
                case "=":
                    memory.put(q.result, getValue(q.arg1));
                    outputLogs.add(String.format("[%d] 👉 赋值: %s = %d", i, q.result, getValue(q.arg1)));
                    break;

                case "+":
                case "-":
                case "*":
                case "/":
                case "%":
                    int v1 = getValue(q.arg1), v2 = getValue(q.arg2), res = 0;
                    if (q.op.equals("+")) res = v1 + v2;
                    else if (q.op.equals("-")) res = v1 - v2;
                    else if (q.op.equals("*")) res = v1 * v2;
                    else if (q.op.equals("/")) res = v2 != 0 ? v1 / v2 : 0;
                    else if (q.op.equals("%")) res = v2 != 0 ? v1 % v2 : 0;
                    memory.put(q.result, res);
                    outputLogs.add(String.format("[%d] 🧮 计算: %s = %d %s %d = %d", i, q.result, v1, q.op, v2, res));
                    break;

                // ================= 新增：处理逻辑运算 =================
                case "&&":
                case "||":
                    int b1 = getValue(q.arg1), b2 = getValue(q.arg2), bRes = 0;
                    if (q.op.equals("&&")) bRes = (b1 != 0 && b2 != 0) ? 1 : 0; // C语言逻辑：非0即真
                    if (q.op.equals("||")) bRes = (b1 != 0 || b2 != 0) ? 1 : 0;
                    memory.put(q.result, bRes);
                    outputLogs.add(String.format("[%d] 🧠 逻辑: %s = %d %s %d = %d", i, q.result, b1, q.op, b2, bRes));
                    break;

                case "CALL":
                    if (q.arg1.equals("write")) {
                        outputLogs.add(String.format("[%d] 🖨️ 控制台输出 (write): %d", i, getValue(q.arg2)));
                    }
                    break;

                case "J":
                    nextI = Integer.parseInt(q.result);
                    outputLogs.add(String.format("[%d] 🔀 无条件跳转 -> %d", i, nextI));
                    break;
                case "J<":
                    if (getValue(q.arg1) < getValue(q.arg2)) {
                        nextI = Integer.parseInt(q.result);
                        outputLogs.add(String.format("[%d] ✔️ 条件成立 (%d < %d), 跳转 -> %d", i, getValue(q.arg1), getValue(q.arg2), nextI));
                    } else {
                        outputLogs.add(String.format("[%d] ❌ 条件不成立 (%d < %d), 继续执行", i, getValue(q.arg1), getValue(q.arg2)));
                    }
                    break;
                case "J>":
                    if (getValue(q.arg1) > getValue(q.arg2)) {
                        nextI = Integer.parseInt(q.result);
                        outputLogs.add(String.format("[%d] ✔️ 条件成立 (%d > %d), 跳转 -> %d", i, getValue(q.arg1), getValue(q.arg2), nextI));
                    }
                    break;
                case "J==":
                    if (getValue(q.arg1) == getValue(q.arg2)) {
                        nextI = Integer.parseInt(q.result);
                        outputLogs.add(String.format("[%d] ✔️ 条件成立 (%d == %d), 跳转 -> %d", i, getValue(q.arg1), getValue(q.arg2), nextI));
                    }
                    break;
            }
            i = nextI;
        }

        if (steps >= maxSteps) outputLogs.add("⚠️ 触发安全限制：疑似死循环，已中止！");
        outputLogs.add("✅ 执行完毕！最终内存状态: " + memory.toString());
        return outputLogs;
    }
}