package com.huangbin.compiler.codegen;

import com.huangbin.compiler.ir.IRGenerator.Quad;
import java.util.*;

/**
 * MASM 16-bit 汇编代码生成器
 * 将四元式中间代码转换为可在 DOSBox + MASM 环境下汇编运行的 .ASM 文件
 *
 * @author 黄彬 (12303070250)
 */
public class CodeGenerator {

    private final List<Quad> quads;
    private final Set<String> variables = new LinkedHashSet<>();
    private final List<String> stringLiterals = new ArrayList<>();   // 按出现顺序
    private final Map<Integer, String> funcStarts = new LinkedHashMap<>(); // quadIdx -> funcName
    private final Map<Integer, Integer> funcRets = new LinkedHashMap<>();  // funcStartIdx -> retQuadIdx
    private final Map<Integer, String[]> funcParams = new LinkedHashMap<>(); // funcStartIdx -> paramNames
    private final Set<Integer> jumpTargets = new LinkedHashSet<>();
    private final Set<String> funcNameSet = new LinkedHashSet<>();
    private static final Set<String> RESERVED = Set.of("write", "write_str", "read", "main");
    private int labelCounter = 0;
    private int strCounter = 0;

    public CodeGenerator(List<Quad> quads) {
        this.quads = quads;
    }

    public String generate() {
        if (quads == null || quads.isEmpty()) return "; 无代码\n";

        firstPass();
        StringBuilder sb = new StringBuilder();
        emitHeader(sb);
        emitDataSection(sb);
        emitCodeStart(sb);
        emitHelpers(sb);
        emitQuads(sb);
        emitFooter(sb);
        return sb.toString();
    }

    // ==================== 第一遍：信息收集 ====================

    private void firstPass() {
        for (int i = 0; i < quads.size(); i++) {
            Quad q = quads.get(i);
            if (q.op.equals("FUNC")) {
                String fn = sanitize(q.arg1);
                funcStarts.put(i, fn);
                funcNameSet.add(fn);
            }
            if (isJumpOp(q.op)) {
                try { jumpTargets.add(Integer.parseInt(q.result)); } catch (NumberFormatException ignored) {}
            }
            collectVar(q.arg1);
            collectVar(q.arg2);
            collectVar(q.result);
        }
        // 建立函数 RET 映射 和 参数信息
        for (Map.Entry<Integer, String> entry : funcStarts.entrySet()) {
            int start = entry.getKey();
            Quad fq = quads.get(start);
            String[] params = (fq.arg2 != null && !fq.arg2.isEmpty())
                ? fq.arg2.split(",") : new String[0];
            funcParams.put(start, params);
            // 参数也是变量
            for (String p : params) variables.add(p.trim());

            for (int i = start + 1; i < quads.size(); i++) {
                if (quads.get(i).op.equals("RET")) { funcRets.put(start, i); break; }
                if (quads.get(i).op.equals("FUNC")) break;
            }
        }
        // 从变量集中移除函数名
        variables.removeAll(funcNameSet);
    }

    private void collectVar(String s) {
        if (s == null || s.equals("_") || s.isEmpty()) return;
        // 处理逗号分隔的参数列表 (来自 FUNC quad 的 arg2)
        if (s.contains(",")) {
            for (String part : s.split(",")) {
                collectVar(part.trim());
            }
            return;
        }
        try { Integer.parseInt(s); return; } catch (NumberFormatException ignored) {}
        if (RESERVED.contains(s)) return;
        variables.add(s);
    }

    private boolean isJumpOp(String op) {
        return op.equals("J") || op.equals("J!=");
    }

    private String sanitize(String name) {
        if (name == null || name.isEmpty()) return name;
        return name.replaceAll("[^a-zA-Z0-9_]", "_");
    }

    // ==================== 输出各部分 ====================

    private void emitHeader(StringBuilder sb) {
        sb.append("; ============================================\n");
        sb.append(";  MASM 16-bit 汇编代码 (自动生成)\n");
        sb.append(";  汇编: masm this.asm;\n");
        sb.append(";  链接: link this.obj;\n");
        sb.append(";  运行: this.exe\n");
        sb.append("; ============================================\n\n");
    }

    private void emitDataSection(StringBuilder sb) {
        sb.append(".MODEL SMALL\n");
        sb.append(".STACK 100h\n\n");
        sb.append(".DATA\n");
        for (String var : variables) {
            sb.append("    _v_").append(var).append("  DW  0\n");
        }
        // 遍历 quads 收集 write_str 中的字符串
        for (Quad q : quads) {
            if (q.op.equals("CALL") && q.arg1.equals("write_str")) {
                stringLiterals.add(q.arg2);
            }
        }
        for (int i = 0; i < stringLiterals.size(); i++) {
            String cleaned = stringLiterals.get(i).replace("'", "").replace("\"", "");
            sb.append("    _s").append(i).append("  DB  '").append(cleaned).append("', '$'\n");
        }
        sb.append("    _newline  DB  0Dh, 0Ah, '$'\n");
        sb.append("    _neg_sign DB  '-', '$'\n");
        sb.append("    _buf_in   DB  8, ?, 8 DUP(0)\n");
        sb.append("\n");
    }

    private void emitCodeStart(StringBuilder sb) {
        sb.append(".CODE\n");
        sb.append("_entry:\n");
        sb.append("    mov  ax, @DATA\n");
        sb.append("    mov  ds, ax\n");
    }

    private void emitHelpers(StringBuilder sb) {
        // ===== write_int: 输出 AX 中的有符号整数 =====
        sb.append("\n");
        sb.append("; --- write_int: 输出 AX 中的有符号整数 (含换行) ---\n");
        sb.append("_write_int PROC\n");
        sb.append("    push bx\n    push cx\n    push dx\n    push si\n");
        sb.append("    mov  si, 0\n");
        sb.append("    cmp  ax, 0\n");
        sb.append("    jge  _wi_pos\n");
        sb.append("    neg  ax\n");
        sb.append("    push ax\n");
        sb.append("    mov  dx, OFFSET _neg_sign\n");
        sb.append("    mov  ah, 09h\n");
        sb.append("    int  21h\n");
        sb.append("    pop  ax\n");
        sb.append("_wi_pos:\n    mov  bx, 10\n");
        sb.append("_wi_loop:\n    mov  dx, 0\n");
        sb.append("    div  bx\n    push dx\n    inc  si\n");
        sb.append("    cmp  ax, 0\n    jne  _wi_loop\n");
        sb.append("_wi_out:\n    pop  dx\n    add  dl, '0'\n    mov  ah, 02h\n    int  21h\n");
        sb.append("    dec  si\n    cmp  si, 0\n    jne  _wi_out\n");
        sb.append("    mov  dx, OFFSET _newline\n    mov  ah, 09h\n    int  21h\n");
        sb.append("    pop  si\n    pop  dx\n    pop  cx\n    pop  bx\n    ret\n");
        sb.append("_write_int ENDP\n\n");

        // ===== read_int: 从键盘读入整数 → AX =====
        sb.append("; --- read_int: 从键盘读取整数 → AX ---\n");
        sb.append("_read_int PROC\n");
        sb.append("    push bx\n    push cx\n    push dx\n    push si\n");
        sb.append("    mov  dx, OFFSET _buf_in\n    mov  ah, 0Ah\n    int  21h\n");
        sb.append("    mov  dx, OFFSET _newline\n    mov  ah, 09h\n    int  21h\n");
        sb.append("    mov  cl, _buf_in + 1\n    mov  ch, 0\n");
        sb.append("    mov  si, OFFSET _buf_in + 2\n    mov  ax, 0\n    mov  bx, 1\n");
        sb.append("    cmp  cx, 0\n    je   _ri_done\n");
        sb.append("    mov  dl, [si]\n    cmp  dl, '-'\n    jne  _ri_parse\n");
        sb.append("    mov  bx, -1\n    inc  si\n    dec  cx\n");
        sb.append("_ri_parse:\n    cmp  cx, 0\n    je   _ri_done\n");
        sb.append("    mov  dl, [si]\n    cmp  dl, '0'\n    jb   _ri_done\n");
        sb.append("    cmp  dl, '9'\n    ja   _ri_done\n");
        sb.append("    sub  dl, '0'\n    mov  dh, 0\n    push dx\n");
        sb.append("    mov  dx, 10\n    mul  dx\n    pop  dx\n    add  ax, dx\n");
        sb.append("    inc  si\n    dec  cx\n    jmp  _ri_parse\n");
        sb.append("_ri_done:\n    cmp  bx, 1\n    je   _ri_exit\n    neg  ax\n");
        sb.append("_ri_exit:\n    pop  si\n    pop  dx\n    pop  cx\n    pop  bx\n    ret\n");
        sb.append("_read_int ENDP\n\n");
    }

    // ==================== 第二遍：四元式 → 汇编 ====================

    private void emitQuads(StringBuilder sb) {
        // 收集哪些 quad 在函数体内
        Set<Integer> funcBodyIndices = new LinkedHashSet<>();
        for (int startIdx : funcStarts.keySet()) {
            Integer retIdx = funcRets.get(startIdx);
            int end = retIdx != null ? retIdx : quads.size() - 1;
            for (int i = startIdx; i <= end; i++) funcBodyIndices.add(i);
        }

        // === 函数定义 ===
        sb.append("    jmp  _after_funcs       ; 跳过函数定义\n\n");
        sb.append("; ===== 函数定义 =====\n");

        List<Integer> sortedStarts = new ArrayList<>(funcStarts.keySet());
        Collections.sort(sortedStarts);

        for (int funcStartIdx : sortedStarts) {
            String funcName = funcStarts.get(funcStartIdx);
            String[] params = funcParams.get(funcStartIdx);
            Integer retIdx = funcRets.get(funcStartIdx);
            int bodyEnd = retIdx != null ? retIdx - 1 : quads.size() - 1;

            sb.append(funcName).append(" PROC\n");
            sb.append("    push bp\n    mov  bp, sp\n");

            // 从栈中复制参数到 .DATA 变量（push 顺序: 先x后y → 栈顶是y, 栈底是x）
            // [bp+4] 是最后 push 的, [bp+4+(n-1)*2] 是最先 push 的
            for (int p = 0; p < params.length; p++) {
                int offset = 4 + (params.length - 1 - p) * 2;
                sb.append("    mov  ax, [bp+").append(offset).append("]\n");
                sb.append("    mov  _v_").append(params[p].trim()).append(", ax\n");
            }
            // 函数体
            for (int i = funcStartIdx + 1; i <= bodyEnd; i++) {
                emitQuadAt(sb, i);
            }
            // RET
            if (retIdx != null) {
                emitLabelIfNeeded(sb, retIdx);
                sb.append("    mov  ax, ").append(resolveVal(quads.get(retIdx).arg1)).append("\n");
            }
            sb.append("    mov  sp, bp\n    pop  bp\n    ret\n");
            sb.append(funcName).append(" ENDP\n\n");
        }

        // === 全局代码 ===
        sb.append("; ===== 入口 & 全局代码 =====\n");
        sb.append("_after_funcs:\n");

        for (int i = 0; i < quads.size(); i++) {
            if (funcBodyIndices.contains(i)) continue;
            emitQuadAt(sb, i);
        }
    }

    private void emitFooter(StringBuilder sb) {
        sb.append("\nEND _entry\n");
    }

    private void emitQuadAt(StringBuilder sb, int i) {
        emitLabelIfNeeded(sb, i);
        Quad q = quads.get(i);

        switch (q.op) {
            case "=":    emitAssign(sb, q); break;
            case "+":    emitArith(sb, q, "add"); break;
            case "-":    emitArith(sb, q, "sub"); break;
            case "*":    emitMul(sb, q); break;
            case "/":    emitDiv(sb, q, false); break;
            case "%":    emitDiv(sb, q, true); break;
            case ">":    emitCmpSet(sb, q, "jg"); break;
            case "<":    emitCmpSet(sb, q, "jl"); break;
            case ">=":   emitCmpSet(sb, q, "jge"); break;
            case "<=":   emitCmpSet(sb, q, "jle"); break;
            case "==":   emitCmpSet(sb, q, "je"); break;
            case "!=":   emitCmpSet(sb, q, "jne"); break;
            case "&&":   emitLogical(sb, q, false); break;
            case "||":   emitLogical(sb, q, true); break;
            case "J":    sb.append("    jmp  label_").append(q.result).append("\n"); break;
            case "J!=":  emitCondJump(sb, q); break;
            case "PARAM": emitPush(sb, q.arg1); break;
            case "CALL": emitCallQuad(sb, q); break;
            case "READ": emitRead(sb, q); break;
            case "EXIT": sb.append("    mov  ah, 4Ch\n    int  21h\n"); break;
        }
    }

    private void emitLabelIfNeeded(StringBuilder sb, int i) {
        if (jumpTargets.contains(i)) {
            sb.append("label_").append(i).append(":\n");
        }
    }

    // ==================== 各指令翻译 ====================

    private void emitAssign(StringBuilder sb, Quad q) {
        sb.append("    mov  ax, ").append(resolveVal(q.arg1)).append("\n");
        sb.append("    mov  _v_").append(q.result).append(", ax\n");
    }

    private void emitArith(StringBuilder sb, Quad q, String op) {
        sb.append("    mov  ax, ").append(resolveVal(q.arg1)).append("\n");
        sb.append("    ").append(op).append("  ax, ").append(resolveVal(q.arg2)).append("\n");
        sb.append("    mov  _v_").append(q.result).append(", ax\n");
    }

    private void emitMul(StringBuilder sb, Quad q) {
        sb.append("    mov  ax, ").append(resolveVal(q.arg1)).append("\n");
        sb.append("    mov  bx, ").append(resolveVal(q.arg2)).append("\n");
        sb.append("    imul bx\n");
        sb.append("    mov  _v_").append(q.result).append(", ax\n");
    }

    private void emitDiv(StringBuilder sb, Quad q, boolean isMod) {
        sb.append("    mov  ax, ").append(resolveVal(q.arg1)).append("\n");
        sb.append("    cwd\n");
        sb.append("    mov  bx, ").append(resolveVal(q.arg2)).append("\n");
        sb.append("    idiv bx\n");
        sb.append("    mov  _v_").append(q.result).append(", ").append(isMod ? "dx" : "ax").append("\n");
    }

    private void emitCmpSet(StringBuilder sb, Quad q, String jmpCond) {
        String lTrue = "_ct" + labelCounter;
        String lEnd  = "_ce" + labelCounter;
        labelCounter++;
        sb.append("    mov  ax, ").append(resolveVal(q.arg1)).append("\n");
        sb.append("    cmp  ax, ").append(resolveVal(q.arg2)).append("\n");
        sb.append("    ").append(jmpCond).append("  ").append(lTrue).append("\n");
        sb.append("    mov  _v_").append(q.result).append(", 0\n");
        sb.append("    jmp  ").append(lEnd).append("\n");
        sb.append(lTrue).append(":\n");
        sb.append("    mov  _v_").append(q.result).append(", 1\n");
        sb.append(lEnd).append(":\n");
    }

    private void emitLogical(StringBuilder sb, Quad q, boolean isOr) {
        String lTrue = "_lt" + labelCounter;
        String lEnd  = "_le" + labelCounter;
        labelCounter++;
        sb.append("    mov  ax, ").append(resolveVal(q.arg1)).append("\n");
        sb.append("    cmp  ax, 0\n");
        if (isOr) {
            sb.append("    jne  ").append(lTrue).append("\n");
            sb.append("    mov  ax, ").append(resolveVal(q.arg2)).append("\n");
            sb.append("    cmp  ax, 0\n");
            sb.append("    jne  ").append(lTrue).append("\n");
            sb.append("    mov  _v_").append(q.result).append(", 0\n");
            sb.append("    jmp  ").append(lEnd).append("\n");
            sb.append(lTrue).append(":\n");
            sb.append("    mov  _v_").append(q.result).append(", 1\n");
        } else {
            sb.append("    je   ").append(lEnd).append("\n");
            sb.append("    mov  ax, ").append(resolveVal(q.arg2)).append("\n");
            sb.append("    cmp  ax, 0\n");
            sb.append("    je   ").append(lEnd).append("\n");
            sb.append("    mov  _v_").append(q.result).append(", 1\n");
            sb.append("    jmp  _lsk").append(labelCounter).append("\n");
            sb.append(lEnd).append(":\n");
            sb.append("    mov  _v_").append(q.result).append(", 0\n");
            sb.append("_lsk").append(labelCounter).append(":\n");
        }
        if (isOr) sb.append(lEnd).append(":\n");
        labelCounter++;
    }

    private void emitCondJump(StringBuilder sb, Quad q) {
        sb.append("    mov  ax, ").append(resolveVal(q.arg1)).append("\n");
        sb.append("    cmp  ax, ").append(resolveVal(q.arg2)).append("\n");
        sb.append("    jne  label_").append(q.result).append("\n");
    }

    private void emitPush(StringBuilder sb, String arg) {
        if (isNumber(arg)) {
            sb.append("    mov  ax, ").append(arg).append("\n");
            sb.append("    push ax\n");
        } else {
            sb.append("    push _v_").append(arg).append("\n");
        }
    }

    private void emitCallQuad(StringBuilder sb, Quad q) {
        if (q.arg1.equals("write")) {
            sb.append("    mov  ax, ").append(resolveVal(q.arg2)).append("\n");
            sb.append("    call _write_int\n");
        } else if (q.arg1.equals("write_str")) {
            int si = findStrIndex(q.arg2);
            sb.append("    mov  dx, OFFSET _s").append(si).append("\n");
            sb.append("    mov  ah, 09h\n    int  21h\n");
        } else {
            String fn = sanitize(q.arg1);
            sb.append("    call ").append(fn).append("\n");
            int pc = parseIntSafe(q.arg2);
            if (pc > 0) sb.append("    add  sp, ").append(pc * 2).append("\n");
            if (!q.result.equals("_")) {
                sb.append("    mov  _v_").append(q.result).append(", ax\n");
            }
        }
    }

    private void emitRead(StringBuilder sb, Quad q) {
        sb.append("    call _read_int\n");
        if (!q.result.equals("_")) {
            sb.append("    mov  _v_").append(q.result).append(", ax\n");
        }
    }

    // ==================== 辅助方法 ====================

    /** 解析操作数：数字→立即数，其他→_v_变量名 */
    private String resolveVal(String s) {
        if (s == null || s.equals("_")) return "0";
        try { Integer.parseInt(s); return s; } catch (NumberFormatException ignored) {}
        return "_v_" + s;
    }

    private boolean isNumber(String s) {
        if (s == null || s.isEmpty() || s.equals("_")) return false;
        try { Integer.parseInt(s); return true; } catch (NumberFormatException e) { return false; }
    }

    private int parseIntSafe(String s) {
        try { return Integer.parseInt(s); } catch (NumberFormatException e) { return 0; }
    }

    private int findStrIndex(String s) {
        for (int i = 0; i < stringLiterals.size(); i++) {
            if (stringLiterals.get(i).equals(s)) return i;
        }
        return 0;
    }
}
