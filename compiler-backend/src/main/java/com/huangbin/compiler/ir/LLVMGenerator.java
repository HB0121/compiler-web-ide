package com.huangbin.compiler.ir;

import java.util.*;

/**
 * LLVM IR 代码生成器 - 将四元式中间代码转换为标准 LLVM IR 文本格式
 *
 * @author 黄彬 (12303070250)
 */
public class LLVMGenerator {

    private final List<IRGenerator.Quad> quads;
    private final Set<String> variables = new LinkedHashSet<>();
    private final Map<Integer, String> funcStarts = new LinkedHashMap<>();
    private final Map<Integer, Integer> funcRets = new LinkedHashMap<>();
    private final Map<Integer, String[]> funcParams = new LinkedHashMap<>();
    private final Set<Integer> jumpTargets = new LinkedHashSet<>();
    private final Set<String> funcNameSet = new LinkedHashSet<>();
    private final Set<String> stringLiterals = new LinkedHashSet<>();
    private static final Set<String> RESERVED = Set.of("write", "write_str", "read", "main");
    private int loadCounter = 1000;

    public LLVMGenerator(List<IRGenerator.Quad> quads) {
        this.quads = quads;
    }

    public String generate() {
        if (quads == null || quads.isEmpty()) return "; 无 LLVM IR 代码\n";

        firstPass();
        StringBuilder sb = new StringBuilder();
        emitHeader(sb);
        emitDeclarations(sb);
        emitFunctions(sb);
        return sb.toString();
    }

    private void firstPass() {
        for (int i = 0; i < quads.size(); i++) {
            IRGenerator.Quad q = quads.get(i);
            if (q.op.equals("FUNC")) {
                funcStarts.put(i, sanitize(q.arg1));
                funcNameSet.add(sanitize(q.arg1));
            }
            if (q.op.equals("J") || q.op.equals("J!=")) {
                try { jumpTargets.add(Integer.parseInt(q.result)); } catch (NumberFormatException ignored) {}
            }
            if (q.arg1 != null && !q.arg1.equals("_") && isVariable(q.arg1)) variables.add(q.arg1);
            if (q.arg2 != null && !q.arg2.equals("_") && isVariable(q.arg2)) variables.add(q.arg2);
            if (q.result != null && !q.result.equals("_") && isVariable(q.result)) variables.add(q.result);
        }

        for (Map.Entry<Integer, String> entry : funcStarts.entrySet()) {
            int start = entry.getKey();
            IRGenerator.Quad fq = quads.get(start);
            String[] params = (fq.arg2 != null && !fq.arg2.isEmpty()) ? fq.arg2.split(",") : new String[0];
            funcParams.put(start, params);
            for (String p : params) variables.add(p.trim());
            for (int i = start + 1; i < quads.size(); i++) {
                if (quads.get(i).op.equals("RET")) { funcRets.put(start, i); break; }
                if (quads.get(i).op.equals("FUNC")) break;
            }
        }
        variables.removeAll(funcNameSet);

        for (IRGenerator.Quad q : quads) {
            if (q.op.equals("CALL") && q.arg1.equals("write_str") && q.arg2 != null) {
                stringLiterals.add(q.arg2);
            }
        }
    }

    private boolean isVariable(String s) {
        try { Integer.parseInt(s); return false; } catch (NumberFormatException ignored) {}
        return !RESERVED.contains(s) && !s.contains(",");
    }

    private String sanitize(String name) {
        if (name == null || name.isEmpty()) return name;
        return name.replaceAll("[^a-zA-Z0-9_]", "_");
    }

    private void emitHeader(StringBuilder sb) {
        sb.append("; ============================================\n");
        sb.append(";  LLVM IR 代码 (自动生成，兼容 LLVM 15+)\n");
        sb.append(";  运行: lli this.ll\n");
        sb.append(";  编译: llc this.ll -o this.s\n");
        sb.append("; ============================================\n\n");
    }

    private void emitDeclarations(StringBuilder sb) {
        sb.append("declare i32 @write_int(i32)\n");
        sb.append("declare i32 @read_int()\n");
        sb.append("declare void @write_str(i8*)\n\n");
    }

    /** 在函数体内为所有变量 alloca */
    private void emitAllocas(StringBuilder sb) {
        for (String v : variables) {
            if (v.equals("_") || v.isEmpty()) continue;
            sb.append("  %_v_").append(v).append(" = alloca i32\n");
        }
    }

    private void emitFunctions(StringBuilder sb) {
        Set<Integer> funcBodyIndices = new LinkedHashSet<>();
        for (int startIdx : funcStarts.keySet()) {
            Integer retIdx = funcRets.get(startIdx);
            int end = retIdx != null ? retIdx : quads.size() - 1;
            for (int i = startIdx; i <= end; i++) funcBodyIndices.add(i);
        }

        List<Integer> globalIndices = new ArrayList<>();
        for (int i = 0; i < quads.size(); i++) {
            if (!funcBodyIndices.contains(i)) globalIndices.add(i);
        }

        List<Integer> sortedStarts = new ArrayList<>(funcStarts.keySet());
        Collections.sort(sortedStarts);

        // 输出用户定义的函数
        for (int funcStartIdx : sortedStarts) {
            String funcName = funcStarts.get(funcStartIdx);
            String[] params = funcParams.get(funcStartIdx);
            Integer retIdx = funcRets.get(funcStartIdx);
            int bodyEnd = retIdx != null ? retIdx : quads.size() - 1;

            sb.append("define i32 @").append(funcName).append("(");
            for (int p = 0; p < params.length; p++) {
                if (p > 0) sb.append(", ");
                sb.append("i32 %").append(params[p].trim());
            }
            sb.append(") {\nentry:\n");
            emitAllocas(sb);
            for (String p : params) {
                sb.append("  store i32 %").append(p.trim()).append(", i32* %_v_").append(p.trim()).append("\n");
            }

            boolean hasRet = false;
            for (int i = funcStartIdx + 1; i <= bodyEnd; i++) {
                if (jumpTargets.contains(i)) {
                    sb.append("  br label %L").append(i).append("\n\nL").append(i).append(":\n");
                }
                emitQuadLLVM(sb, quads.get(i), i);
                if (quads.get(i).op.equals("RET")) hasRet = true;
            }
            if (!hasRet) sb.append("  ret i32 0\n");
            sb.append("}\n\n");
        }

        // 全局代码（CALL main, EXIT 等）
        if (!globalIndices.isEmpty()) {
            sb.append("define i32 @__global_main() {\nentry:\n");
            emitAllocas(sb);
            for (int i : globalIndices) {
                if (jumpTargets.contains(i)) {
                    sb.append("  br label %L").append(i).append("\n\nL").append(i).append(":\n");
                }
                emitQuadLLVM(sb, quads.get(i), i);
            }
            sb.append("  ret i32 0\n}\n\n");
        }

        // 如果用户没有定义 main，生成入口包装
        if (!funcNameSet.contains("main")) {
            sb.append("define i32 @main() {\nentry:\n");
            if (!globalIndices.isEmpty()) {
                sb.append("  %entry_call = call i32 @__global_main()\n");
            }
            sb.append("  ret i32 0\n}\n");
        }
    }

    // ==================== 四元式 → LLVM IR ====================

    private void emitQuadLLVM(StringBuilder sb, IRGenerator.Quad q, int idx) {
        switch (q.op) {
            case "=":
                emitStore(sb, q.result, loadOperand(sb, q.arg1, idx));
                break;
            case "+":
                emitArithStore(sb, q, idx, "add");
                break;
            case "-":
                if (q.arg1.equals("0")) {
                    String v = loadOperand(sb, q.arg2, idx);
                    sb.append("  %t").append(idx).append(" = sub i32 0, ").append(v).append("\n");
                } else {
                    emitArithStore(sb, q, idx, "sub");
                }
                break;
            case "*":
                emitArithStore(sb, q, idx, "mul");
                break;
            case "/":
                emitArithStore(sb, q, idx, "sdiv");
                break;
            case "%":
                emitArithStore(sb, q, idx, "srem");
                break;
            case ">": case "<": case ">=": case "<=": case "==": case "!=":
                emitCmpStore(sb, q, idx);
                break;
            case "&&": case "||":
                emitLogicalStore(sb, q, idx);
                break;
            case "J":
                sb.append("  br label %L").append(q.result).append("\n");
                break;
            case "J!=":
                emitCondBr(sb, q, idx);
                break;
            case "PARAM":
                emitParam(sb, q.arg1, idx);
                break;
            case "CALL":
                emitCallQuad(sb, q, idx);
                break;
            case "READ":
                sb.append("  %rd").append(idx).append(" = call i32 @read_int()\n");
                if (!q.result.equals("_")) emitStore(sb, q.result, "%rd" + idx);
                break;
            case "RET":
                sb.append("  ret i32 ").append(loadOperand(sb, q.arg1, idx)).append("\n");
                break;
            case "EXIT":
                sb.append("  ret i32 0\n");
                break;
        }
    }

    // ==================== 辅助方法 ====================

    /** 加载操作数：常数直接返回，变量先从 alloca load */
    private String loadOperand(StringBuilder sb, String arg, int idx) {
        if (arg == null || arg.equals("_")) return "0";
        try { Integer.parseInt(arg); return arg; } catch (NumberFormatException ignored) {}
        // 是变量，需要 load
        int lc = loadCounter++;
        sb.append("  %l").append(lc).append(" = load i32, i32* %_v_").append(arg).append("\n");
        return "%l" + lc;
    }

    /** 不加载，直接用于 ret / alloca 地址等场景 */
    private String rawVal(String s) {
        if (s == null || s.equals("_")) return "0";
        try { Integer.parseInt(s); return s; } catch (NumberFormatException ignored) {}
        return "%_v_" + s;
    }

    /** 将值 store 到目标变量 */
    private void emitStore(StringBuilder sb, String target, String value) {
        sb.append("  store i32 ").append(value).append(", i32* %_v_").append(target).append("\n");
    }

    /** 二元运算：load → 计算 → store */
    private void emitArithStore(StringBuilder sb, IRGenerator.Quad q, int idx, String llvmOp) {
        String v1 = loadOperand(sb, q.arg1, idx);
        String v2 = loadOperand(sb, q.arg2, idx);
        sb.append("  %t").append(idx).append(" = ").append(llvmOp).append(" i32 ").append(v1).append(", ").append(v2).append("\n");
        emitStore(sb, q.result, "%t" + idx);
    }

    /** 比较运算：load → icmp → zext → store */
    private void emitCmpStore(StringBuilder sb, IRGenerator.Quad q, int idx) {
        String v1 = loadOperand(sb, q.arg1, idx);
        String v2 = loadOperand(sb, q.arg2, idx);
        Map<String, String> cmps = Map.of(
            ">", "sgt", "<", "slt", ">=", "sge", "<=", "sle", "==", "eq", "!=", "ne"
        );
        sb.append("  %t").append(idx).append(" = icmp ").append(cmps.get(q.op)).append(" i32 ").append(v1).append(", ").append(v2).append("\n");
        sb.append("  %tz").append(idx).append(" = zext i1 %t").append(idx).append(" to i32\n");
        emitStore(sb, q.result, "%tz" + idx);
    }

    /** 逻辑运算：load → icmp ne 0 → and/or → zext → store */
    private void emitLogicalStore(StringBuilder sb, IRGenerator.Quad q, int idx) {
        String v1 = loadOperand(sb, q.arg1, idx);
        String v2 = loadOperand(sb, q.arg2, idx);
        sb.append("  %ta").append(idx).append(" = icmp ne i32 ").append(v1).append(", 0\n");
        sb.append("  %tb").append(idx).append(" = icmp ne i32 ").append(v2).append(", 0\n");
        String llvmOp = q.op.equals("&&") ? "and" : "or";
        sb.append("  %t").append(idx).append(" = ").append(llvmOp).append(" i1 %ta").append(idx).append(", %tb").append(idx).append("\n");
        sb.append("  %tz").append(idx).append(" = zext i1 %t").append(idx).append(" to i32\n");
        emitStore(sb, q.result, "%tz" + idx);
    }

    /** 条件跳转 */
    private void emitCondBr(StringBuilder sb, IRGenerator.Quad q, int idx) {
        String v1 = loadOperand(sb, q.arg1, idx);
        String v2 = loadOperand(sb, q.arg2, idx);
        sb.append("  %tj").append(idx).append(" = icmp ne i32 ").append(v1).append(", ").append(v2).append("\n");
        sb.append("  br i1 %tj").append(idx).append(", label %L").append(q.result).append(", label %L_next").append(idx).append("\n\n");
        sb.append("L_next").append(idx).append(":\n");
    }

    /** 参数传递：变量 load，常量用 add 0 */
    private void emitParam(StringBuilder sb, String arg, int idx) {
        if (arg == null || arg.equals("_")) {
            sb.append("  %p").append(idx).append(" = add i32 0, 0\n");
            return;
        }
        try {
            int v = Integer.parseInt(arg);
            sb.append("  %p").append(idx).append(" = add i32 0, ").append(v).append("\n");
        } catch (NumberFormatException e) {
            sb.append("  %p").append(idx).append(" = ").append(loadOperand(sb, arg, idx)).append("\n");
        }
    }

    /** 函数调用 */
    private void emitCallQuad(StringBuilder sb, IRGenerator.Quad q, int idx) {
        if (q.arg1.equals("write")) {
            String v = loadOperand(sb, q.arg2, idx);
            sb.append("  call i32 @write_int(i32 ").append(v).append(")\n");
        } else if (q.arg1.equals("write_str")) {
            sb.append("  ; write_str: ").append(q.arg2).append("\n");
        } else {
            // 收集前面 PARAM 的值
            int paramCount = parseIntSafe(q.arg2);
            List<String> args = new ArrayList<>();
            for (int j = idx - paramCount; j < idx; j++) {
                if (quads.get(j).op.equals("PARAM")) {
                    args.add("%p" + j);
                }
            }
            String funcName = sanitize(q.arg1);
            sb.append("  %cf").append(idx).append(" = call i32 @").append(funcName).append("(");
            for (int a = 0; a < args.size(); a++) {
                if (a > 0) sb.append(", ");
                sb.append("i32 ").append(args.get(a));
            }
            sb.append(")\n");
            if (!q.result.equals("_")) emitStore(sb, q.result, "%cf" + idx);
        }
    }

    private int parseIntSafe(String s) {
        try { return Integer.parseInt(s); } catch (NumberFormatException e) { return 0; }
    }
}
