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
            return memory.getOrDefault(arg, 0); // 如果是变量，去内存里找
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
                    outputLogs.add(String.format("👉 执行赋值: 变量 %s 的值变为 %d", q.result, val));
                    break;
                case "+":
                    memory.put(q.result, getValue(q.arg1) + getValue(q.arg2));
                    break;
                // 以后如果你加了 JUMP 指令，这里可以直接修改 i 的值来实现循环和分支！
            }
        }

        outputLogs.add("✅ 执行完毕！最终内存状态: " + memory.toString());
        return outputLogs;
    }
}