package com.huangbin.compiler.interpreter;

import com.huangbin.compiler.ir.IRGenerator.Quad;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Interpreter {

    private final List<Quad> quads;
    private final Map<String, Integer> memory = new HashMap<>(); // 模拟运行内存
    private final List<String> outputLogs = new ArrayList<>();   // 记录运行日志

    public Interpreter(List<Quad> quads) {
        this.quads = quads;
    }

    // 辅助方法：判断是变量还是数字
    private int getValue(String arg) {
        if (arg == null || arg.equals("_")) return 0;
        try {
            return Integer.parseInt(arg); // 如果是纯数字，直接返回
        } catch (NumberFormatException e) {
            return memory.getOrDefault(arg, 0); // 如果是变量，去内存里找，找不到默认返回 0
        }
    }

    // 核心执行引擎
    public List<String> run() {
        outputLogs.add("🚀 开始解释执行中间代码...");

        for (int i = 0; i < quads.size(); i++) {
            Quad q = quads.get(i);

            switch (q.op) {
                case "=":
                    int val = getValue(q.arg1);
                    memory.put(q.result, val);
                    outputLogs.add(String.format("👉 赋值: 变量 %s = %d", q.result, val));
                    break;

                case "+":
                    int sum = getValue(q.arg1) + getValue(q.arg2);
                    memory.put(q.result, sum);
                    outputLogs.add(String.format("🧮 计算: %s = %d + %d = %d", q.result, getValue(q.arg1), getValue(q.arg2), sum));
                    break;

                case "-":
                    int diff = getValue(q.arg1) - getValue(q.arg2);
                    memory.put(q.result, diff);
                    outputLogs.add(String.format("🧮 计算: %s = %d - %d = %d", q.result, getValue(q.arg1), getValue(q.arg2), diff));
                    break;

                case "*":
                    int prod = getValue(q.arg1) * getValue(q.arg2);
                    memory.put(q.result, prod);
                    outputLogs.add(String.format("🧮 计算: %s = %d * %d = %d", q.result, getValue(q.arg1), getValue(q.arg2), prod));
                    break;

                case "/":
                    int divisor = getValue(q.arg2);
                    if (divisor != 0) {
                        int quotient = getValue(q.arg1) / divisor;
                        memory.put(q.result, quotient);
                        outputLogs.add(String.format("🧮 计算: %s = %d / %d = %d", q.result, getValue(q.arg1), divisor, quotient));
                    } else {
                        outputLogs.add("❌ 运行时错误: 除数不能为 0");
                    }
                    break;
            }
        }

        outputLogs.add("✅ 执行完毕！最终内存状态: " + memory.toString());
        return outputLogs;
    }
}