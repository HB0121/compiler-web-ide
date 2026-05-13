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

    // 【核心黑科技】：打印缓冲区，专门用来画图形！
    private final StringBuilder consoleBuffer = new StringBuilder();

    public Interpreter(List<Quad> quads) { this.quads = quads; }

    private int getValue(String arg) {
        if (arg == null || arg.equals("_")) return 0;
        try { return Integer.parseInt(arg); }
        catch (NumberFormatException e) { return memory.getOrDefault(arg, 0); }
    }

    public List<String> run() {
        outputLogs.add("🚀 开始解释执行...");
        int maxSteps = 5000; // 图形打印步数会比较多
        int steps = 0;

        for (int i = 0; i < quads.size() && steps < maxSteps; steps++) {
            Quad q = quads.get(i);
            int nextI = i + 1;

            switch (q.op) {
                case "=": memory.put(q.result, getValue(q.arg1)); break;

                case "+": case "-": case "*": case "/": case "%":
                    int v1 = getValue(q.arg1), v2 = getValue(q.arg2), res = 0;
                    if (q.op.equals("+")) res = v1 + v2;
                    else if (q.op.equals("-")) res = v1 - v2;
                    else if (q.op.equals("*")) res = v1 * v2;
                    else if (q.op.equals("/")) res = v2 != 0 ? v1 / v2 : 0;
                    else if (q.op.equals("%")) res = v2 != 0 ? v1 % v2 : 0;
                    memory.put(q.result, res);
                    break;

                case "&&": case "||":
                    int b1 = getValue(q.arg1), b2 = getValue(q.arg2), bRes = 0;
                    if (q.op.equals("&&")) bRes = (b1 != 0 && b2 != 0) ? 1 : 0;
                    if (q.op.equals("||")) bRes = (b1 != 0 || b2 != 0) ? 1 : 0;
                    memory.put(q.result, bRes); break;

                case ">": case "<": case ">=": case "<=": case "==": case "!=":
                    int cv1 = getValue(q.arg1), cv2 = getValue(q.arg2), cRes = 0;
                    if (q.op.equals(">")) cRes = cv1 > cv2 ? 1 : 0;
                    if (q.op.equals("<")) cRes = cv1 < cv2 ? 1 : 0;
                    if (q.op.equals(">=")) cRes = cv1 >= cv2 ? 1 : 0;
                    if (q.op.equals("<=")) cRes = cv1 <= cv2 ? 1 : 0;
                    if (q.op.equals("==")) cRes = cv1 == cv2 ? 1 : 0;
                    if (q.op.equals("!=")) cRes = cv1 != cv2 ? 1 : 0;
                    memory.put(q.result, cRes); break;

                // 【新增】处理键盘输入：自动为你填入 9，用来完美测试九九乘法表和三角形！
                case "READ":
                    int simulatedInput = 9;
                    memory.put(q.result, simulatedInput);
                    outputLogs.add(String.format("👉 遇到 read()，系统自动模拟输入 -> %d", simulatedInput));
                    break;

                // 【新增】带缓冲的控制台画图引擎
                case "CALL":
                    if (q.arg1.equals("write")) {
                        consoleBuffer.append(getValue(q.arg2)); // 拼接数字
                    } else if (q.arg1.equals("write_str")) {
                        // 剥离所有的单引号和双引号
                        String str = q.arg2.replace("'", "").replace("\"", "");
                        if (str.equals("\\n") || str.equals("换行")) {
                            // 遇到换行指令，将积累的图形整行打印出去，清空画布
                            outputLogs.add("🖨️: " + consoleBuffer.toString());
                            consoleBuffer.setLength(0);
                        } else {
                            consoleBuffer.append(str); // 拼接字符
                        }
                    }
                    break;

                case "J": nextI = Integer.parseInt(q.result); break;

                case "J!=":
                    if (getValue(q.arg1) != getValue(q.arg2)) nextI = Integer.parseInt(q.result);
                    break;
            }
            i = nextI;
        }

        // 扫尾：如果缓冲区里还有没被 \n 刷出来的字，打出来
        if (consoleBuffer.length() > 0) {
            outputLogs.add("🖨️: " + consoleBuffer.toString());
        }

        if (steps >= maxSteps) outputLogs.add("⚠️ 警告：检测到无限循环，已自动停止执行。");
        outputLogs.add("✅ 解释执行完毕！最终符号表状态: " + memory.toString());
        return outputLogs;
    }
}