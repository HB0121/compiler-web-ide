package com.huangbin.compiler.interpreter;

import com.huangbin.compiler.ir.IRGenerator.Quad;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Stack;

public class Interpreter {

    private final List<Quad> quads;
    private final List<String> outputLogs = new ArrayList<>();
    private final StringBuilder consoleBuffer = new StringBuilder();

    // 【核心黑科技】：函数调用活动记录栈 (Activation Record)
    private static class Frame {
        public Map<String, Integer> memory = new HashMap<>();
        public int retAddr;
        public String retTarget;
    }

    private final Stack<Frame> callStack = new Stack<>();
    private final Map<String, Integer> globalMemory = new HashMap<>(); // 存放全局变量
    private final Map<String, Integer> funcMap = new HashMap<>(); // 函数入口映射表
    private final List<Integer> paramBuffer = new ArrayList<>(); // 参数传递缓存区

    public Interpreter(List<Quad> quads) {
        this.quads = quads;
        // 初始化阶段：扫描所有 FUNC 指令，记录函数名对应的行号
        for (int i = 0; i < quads.size(); i++) {
            if (quads.get(i).op.equals("FUNC")) {
                funcMap.put(quads.get(i).arg1, i);
            }
        }
    }

    // 智能寻址：优先找当前函数的局部变量，找不到再找全局变量
    private int getValue(String arg) {
        if (arg == null || arg.equals("_")) return 0;
        try { return Integer.parseInt(arg); } catch (NumberFormatException ignored) {}
        if (!callStack.isEmpty() && callStack.peek().memory.containsKey(arg)) return callStack.peek().memory.get(arg);
        return globalMemory.getOrDefault(arg, 0);
    }

    // 智能赋值：如果有栈帧就赋给局部变量，否则赋给全局变量
    private void setValue(String arg, int val) {
        if (callStack.isEmpty()) globalMemory.put(arg, val);
        else callStack.peek().memory.put(arg, val);
    }

    public List<String> run() {
        outputLogs.add("🚀 开始解释执行 (已启用调用栈机制)...");
        int maxSteps = 10000; // 递归调用消耗步数较大
        int steps = 0;

        for (int i = 0; i < quads.size() && steps < maxSteps; steps++) {
            Quad q = quads.get(i);
            int nextI = i + 1;

            switch (q.op) {
                case "FUNC": break; // 只是个标签，直接跳过
                case "=": setValue(q.result, getValue(q.arg1)); break;

                case "+": case "-": case "*": case "/": case "%":
                    int v1 = getValue(q.arg1), v2 = getValue(q.arg2), res = 0;
                    if (q.op.equals("+")) res = v1 + v2;
                    else if (q.op.equals("-")) res = v1 - v2;
                    else if (q.op.equals("*")) res = v1 * v2;
                    else if (q.op.equals("/")) res = v2 != 0 ? v1 / v2 : 0;
                    else if (q.op.equals("%")) res = v2 != 0 ? v1 % v2 : 0;
                    setValue(q.result, res); break;

                case "&&": case "||":
                    int b1 = getValue(q.arg1), b2 = getValue(q.arg2), bRes = 0;
                    if (q.op.equals("&&")) bRes = (b1 != 0 && b2 != 0) ? 1 : 0;
                    if (q.op.equals("||")) bRes = (b1 != 0 || b2 != 0) ? 1 : 0;
                    setValue(q.result, bRes); break;

                case ">": case "<": case ">=": case "<=": case "==": case "!=":
                    int cv1 = getValue(q.arg1), cv2 = getValue(q.arg2), cRes = 0;
                    if (q.op.equals(">")) cRes = cv1 > cv2 ? 1 : 0;
                    if (q.op.equals("<")) cRes = cv1 < cv2 ? 1 : 0;
                    if (q.op.equals(">=")) cRes = cv1 >= cv2 ? 1 : 0;
                    if (q.op.equals("<=")) cRes = cv1 <= cv2 ? 1 : 0;
                    if (q.op.equals("==")) cRes = cv1 == cv2 ? 1 : 0;
                    if (q.op.equals("!=")) cRes = cv1 != cv2 ? 1 : 0;
                    setValue(q.result, cRes); break;

                // 【核心升级】：处理参数压栈、函数调用与弹栈
                case "PARAM":
                    paramBuffer.add(getValue(q.arg1)); // 把计算好的参数压入暂存区
                    break;

                case "CALL":
                    if (q.arg1.equals("write")) {
                        consoleBuffer.append(getValue(q.arg2));
                    } else if (q.arg1.equals("write_str")) {
                        String str = q.arg2.replace("'", "").replace("\"", "");
                        if (str.equals("\\n") || str.equals("换行")) {
                            outputLogs.add("🖨️: " + consoleBuffer.toString()); consoleBuffer.setLength(0);
                        } else consoleBuffer.append(str);
                    } else {
                        // 真正的自定义函数调用！
                        int targetIdx = funcMap.getOrDefault(q.arg1, -1);
                        if (targetIdx == -1) { outputLogs.add("❌ 错误：找不到函数 " + q.arg1); break; }

                        Frame newFrame = new Frame();
                        newFrame.retAddr = nextI; // 记住回来执行哪一行
                        newFrame.retTarget = q.result; // 记住返回值赋给谁

                        // 从函数定义四元式中提取形参名称，并与暂存区的实参一一对应！
                        Quad funcDefQuad = quads.get(targetIdx);
                        String[] paramNames = funcDefQuad.arg2.isEmpty() ? new String[0] : funcDefQuad.arg2.split(",");
                        for (int p = 0; p < paramNames.length && p < paramBuffer.size(); p++) {
                            newFrame.memory.put(paramNames[p], paramBuffer.get(p));
                        }
                        paramBuffer.clear(); // 用完清空缓存区

                        callStack.push(newFrame); // 新建作用域栈帧，完美保护现场
                        nextI = targetIdx + 1; // 飞身跳转到函数体去执行！
                    }
                    break;

                case "RET":
                    int retVal = getValue(q.arg1);
                    if (!callStack.isEmpty()) {
                        Frame oldFrame = callStack.pop(); // 销毁当前函数作用域
                        if (!oldFrame.retTarget.equals("_")) {
                            setValue(oldFrame.retTarget, retVal); // 将返回值带给上一层函数
                        }
                        nextI = oldFrame.retAddr; // 时光倒流，回到调用前的地方
                    }
                    break;

                case "READ":
                    setValue(q.result, 9); // 系统自动模拟键盘输入 9
                    break;

                case "J": nextI = Integer.parseInt(q.result); break;
                case "J!=": if (getValue(q.arg1) != getValue(q.arg2)) nextI = Integer.parseInt(q.result); break;
                case "EXIT": nextI = quads.size(); break; // 执行完毕，优雅退出
            }
            i = nextI;
        }

        if (consoleBuffer.length() > 0) outputLogs.add("🖨️: " + consoleBuffer.toString());
        if (steps >= maxSteps) outputLogs.add("⚠️ 警告：检测到过度递归或无限循环，已安全阻断！");
        outputLogs.add("✅ 执行成功！结束时全局变量状态: " + globalMemory.toString());
        return outputLogs;
    }
}