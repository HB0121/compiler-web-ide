package com.huangbin.compiler.codegen;

import com.huangbin.compiler.ir.IRGenerator.Quad;
import java.util.*;

/**
 * MASM 16-bit 汇编代码生成器
 * 将四元式中间代码转换为可在 DOSBox + MASM 环境下汇编运行的 .ASM 文件
 */
public class CodeGenerator {

    private final List<Quad> quads;
    private final Set<String> variables = new LinkedHashSet<>();
    private final Set<String> stringLiterals = new LinkedHashSet<>();
    private final Map<Integer, String> funcStarts = new LinkedHashMap<>(); // quadIdx -> funcName
    private final Map<Integer, Integer> funcRets = new LinkedHashMap<>();   // funcStartIdx -> retQuadIdx
    private final Set<Integer> jumpTargets = new LinkedHashSet<>();
    private int labelCounter = 0;

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
        return sb.toString();
    }

    // ==================== 第一遍：信息收集 ====================

    private void firstPass() {
        for (int i = 0; i < quads.size(); i++) {
            Quad q = quads.get(i);
            // 收集函数定义
            if (q.op.equals("FUNC")) {
                funcStarts.put(i, sanitizeName(q.arg1));
            }
            // 收集跳转目标
            if (isJumpOp(q.op)) {
                try { jumpTargets.add(Integer.parseInt(q.result)); } catch (NumberFormatException ignored) {}
            }
            // 收集字符串
            if (q.op.equals("write_str")) {
                stringLiterals.add(q.arg2);
            }
            // 收集变量
            collectVar(q.arg1);
            collectVar(q.arg2);
            collectVar(q.result);
        }
        // 建立函数 RET 映射
        for (Map.Entry<Integer, String> entry : funcStarts.entrySet()) {
            int start = entry.getKey();
            for (int i = start + 1; i < quads.size(); i++) {
                if (quads.get(i).op.equals("RET")) {
                    funcRets.put(start, i);
                    break;
                }
                if (quads.get(i).op.equals("FUNC")) break; // 下一个函数开始了，说明这个函数没 RET（异常情况）
            }
        }
        // 从变量集中移除函数名
        for (String fn : funcStarts.values()) {
            variables.remove(fn);
        }
    }

    private void collectVar(String s) {
        if (s == null || s.equals("_") || s.isEmpty()) return;
        // 是数字吗？
        try { Integer.parseInt(s); return; } catch (NumberFormatException ignored) {}
        // 不是函数名或关键字 → 就是变量
        if (!funcStarts.containsValue(s) && !isKeyword(s)) {
            variables.add(s);
        }
    }

    private boolean isKeyword(String s) {
        return Set.of("write", "write_str", "read", "main").contains(s);
    }

    private boolean isJumpOp(String op) {
        return op.equals("J") || op.equals("J!=") || op.equals("J>") || op.equals("J<")
            || op.equals("J>=") || op.equals("J<=") || op.equals("J==") || op.equals("J!=");
    }

    private String sanitizeName(String name) {
        // MASM 标识符不能有特殊字符，保留原始名称（用户代码不会用特殊字符）
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
            sb.append("    ").append(var).append("  DW  0\n");
        }
        // 字符串常量
        int strIdx = 0;
        for (String str : stringLiterals) {
            String cleaned = str.replace("'", "").replace("\"", "");
            sb.append("    _str").append(strIdx).append("  DB  '").append(cleaned).append("', '$'\n");
            strIdx++;
        }
        sb.append("    _newline  DB  0Dh, 0Ah, '$'\n");
        sb.append("    _neg_sign DB  '-', '$'\n");
        sb.append("    _buf_out  DB  8 DUP(0), '$'\n");
        sb.append("    _buf_in   DB  8, ?, 8 DUP(0)\n");
        sb.append("\n");
    }

    private void emitCodeStart(StringBuilder sb) {
        sb.append(".CODE\n");
        // 初始化 DS
        sb.append("_entry:\n");
        sb.append("    mov  ax, @DATA\n");
        sb.append("    mov  ds, ax\n");
    }

    private void emitHelpers(StringBuilder sb) {
        // ===== write_int: 输出 AX 中的有符号整数 =====
        sb.append("\n");
        sb.append("; ----------------------------------------\n");
        sb.append("; 输出 AX 中的有符号整数 (十进制)\n");
        sb.append("; ----------------------------------------\n");
        sb.append("_write_int PROC\n");
        sb.append("    push bx\n    push cx\n    push dx\n    push si\n");
        sb.append("    mov  si, 0               ; si=数字位数\n");
        sb.append("    cmp  ax, 0\n");
        sb.append("    jge  _wi_pos\n");
        sb.append("    neg  ax                  ; 取绝对值\n");
        sb.append("    push ax\n");
        sb.append("    mov  dx, OFFSET _neg_sign\n");
        sb.append("    mov  ah, 09h\n");
        sb.append("    int  21h                 ; 输出负号\n");
        sb.append("    pop  ax\n");
        sb.append("_wi_pos:\n");
        sb.append("    mov  bx, 10\n");
        sb.append("_wi_loop:\n");
        sb.append("    mov  dx, 0\n");
        sb.append("    div  bx                  ; AX/BX → 商AX, 余数DX\n");
        sb.append("    push dx                  ; 余数(数字)压栈\n");
        sb.append("    inc  si\n");
        sb.append("    cmp  ax, 0\n");
        sb.append("    jne  _wi_loop\n");
        sb.append("_wi_output:\n");
        sb.append("    pop  dx\n");
        sb.append("    add  dl, '0'\n");
        sb.append("    mov  ah, 02h\n");
        sb.append("    int  21h                 ; 输出一个字符\n");
        sb.append("    dec  si\n");
        sb.append("    cmp  si, 0\n");
        sb.append("    jne  _wi_output\n");
        // 换行
        sb.append("    mov  dx, OFFSET _newline\n");
        sb.append("    mov  ah, 09h\n");
        sb.append("    int  21h\n");
        sb.append("    pop  si\n    pop  dx\n    pop  cx\n    pop  bx\n");
        sb.append("    ret\n");
        sb.append("_write_int ENDP\n\n");

        // ===== read_int: 从键盘读入整数 → AX =====
        sb.append("; ----------------------------------------\n");
        sb.append("; 从键盘读入整数，结果存入 AX\n");
        sb.append("; ----------------------------------------\n");
        sb.append("_read_int PROC\n");
        sb.append("    push bx\n    push cx\n    push dx\n    push si\n");
        sb.append("    mov  dx, OFFSET _buf_in\n");
        sb.append("    mov  ah, 0Ah\n");
        sb.append("    int  21h                 ; DOS 缓冲输入\n");
        sb.append("    mov  dx, OFFSET _newline\n");
        sb.append("    mov  ah, 09h\n");
        sb.append("    int  21h                 ; 换行\n");
        sb.append("    mov  si, OFFSET _buf_in + 2  ; 指向输入字符\n");
        sb.append("    mov  cl, _buf_in + 1     ; 实际读入的字符数\n");
        sb.append("    mov  ch, 0\n");
        sb.append("    mov  ax, 0\n");
        sb.append("    mov  bx, 1               ; 符号标志: 1=正, -1=负\n");
        sb.append("    cmp  cx, 0\n");
        sb.append("    je   _ri_done\n");
        sb.append("    mov  dl, [si]\n");
        sb.append("    cmp  dl, '-'\n");
        sb.append("    jne  _ri_parse\n");
        sb.append("    mov  bx, -1\n");
        sb.append("    inc  si\n");
        sb.append("    dec  cx\n");
        sb.append("_ri_parse:\n");
        sb.append("    cmp  cx, 0\n");
        sb.append("    je   _ri_done\n");
        sb.append("    mov  dl, [si]\n");
        sb.append("    cmp  dl, '0'\n");
        sb.append("    jb   _ri_done\n");
        sb.append("    cmp  dl, '9'\n");
        sb.append("    ja   _ri_done\n");
        sb.append("    sub  dl, '0'\n");
        sb.append("    mov  dh, 0\n");
        sb.append("    push dx                  ; 先保存当前位\n");
        sb.append("    mov  dx, 10\n");
        sb.append("    mul  dx                  ; AX = AX * 10\n");
        sb.append("    pop  dx\n");
        sb.append("    add  ax, dx              ; AX = AX + 当前位\n");
        sb.append("    inc  si\n");
        sb.append("    dec  cx\n");
        sb.append("    jmp  _ri_parse\n");
        sb.append("_ri_done:\n");
        sb.append("    cmp  bx, 1\n");
        sb.append("    je   _ri_exit\n");
        sb.append("    neg  ax\n");
        sb.append("_ri_exit:\n");
        sb.append("    pop  si\n    pop  dx\n    pop  cx\n    pop  bx\n");
        sb.append("    ret\n");
        sb.append("_read_int ENDP\n\n");
    }

    // ==================== 第二遍：四元式 → 汇编 ====================

    private void emitQuads(StringBuilder sb) {
        // 找出"全局代码"的起始位置（跳转到跳过所有函数定义后的第一个全局 quad）
        // 并找出函数定义的结束位置
        int lastFuncEnd = -1;
        for (Map.Entry<Integer, Integer> e : funcRets.entrySet()) {
            if (e.getValue() > lastFuncEnd) lastFuncEnd = e.getValue();
        }

        // 首先发射函数定义
        sb.append("; ===== 函数定义 =====\n");
        sb.append("    jmp  _after_funcs       ; 跳过函数定义\n\n");

        List<Integer> funcStartList = new ArrayList<>(funcStarts.keySet());
        Collections.sort(funcStartList);

        for (int funcStartIdx : funcStartList) {
            String funcName = funcStarts.get(funcStartIdx);
            Quad funcQuad = quads.get(funcStartIdx);
            String[] params = funcQuad.arg2 != null && !funcQuad.arg2.isEmpty()
                ? funcQuad.arg2.split(",") : new String[0];

            sb.append(funcName).append(" PROC\n");
            sb.append("    push bp\n");
            sb.append("    mov  bp, sp\n");

            // 发射函数体内的四元式 (FUNC之后到RET之前)
            Integer retIdx = funcRets.get(funcStartIdx);
            int bodyEnd = retIdx != null ? retIdx - 1 : quads.size() - 1;

            for (int i = funcStartIdx + 1; i <= bodyEnd; i++) {
                emitQuadAt(sb, i, params);
            }
            // RET
            if (retIdx != null && retIdx < quads.size()) {
                emitLabelIfNeeded(sb, retIdx);
                Quad retQ = quads.get(retIdx);
                String val = isNumber(retQ.arg1) ? retQ.arg1 : loadToAX(retQ.arg1);
                sb.append("    mov  ax, ").append(val).append("\n");
            } else {
                sb.append("    mov  ax, 0\n");
            }
            sb.append("    mov  sp, bp\n");
            sb.append("    pop  bp\n");
            sb.append("    ret\n");
            sb.append(funcName).append(" ENDP\n\n");
        }

        // 发射全局代码
        sb.append("; ===== 入口 & 全局代码 =====\n");
        sb.append("_after_funcs:\n");

        // 收集属于全局的 quad 索引
        Set<Integer> funcBodyIndices = new LinkedHashSet<>();
        for (int startIdx : funcStarts.keySet()) {
            Integer retIdx = funcRets.get(startIdx);
            int end = retIdx != null ? retIdx : quads.size() - 1;
            for (int i = startIdx; i <= end; i++) {
                funcBodyIndices.add(i);
            }
        }

        for (int i = 0; i < quads.size(); i++) {
            if (funcBodyIndices.contains(i)) continue; // 已在函数定义中处理
            emitQuadAt(sb, i, new String[0]);
        }
    }

    private void emitQuadAt(StringBuilder sb, int i, String[] params) {
        emitLabelIfNeeded(sb, i);
        Quad q = quads.get(i);

        switch (q.op) {
            case "FUNC": break; // 已单独处理
            case "RET":  break; // 已单独处理
            case "=":    emitAssign(sb, q); break;
            case "+":    emitArith(sb, q, "add"); break;
            case "-":    emitArith(sb, q, "sub"); break;
            case "*":    emitMul(sb, q); break;
            case "/":    emitDiv(sb, q, false); break;
            case "%":    emitDiv(sb, q, true); break;
            case ">":    emitCmpSet(sb, q, "jg", "jle"); break;
            case "<":    emitCmpSet(sb, q, "jl", "jge"); break;
            case ">=":   emitCmpSet(sb, q, "jge", "jl"); break;
            case "<=":   emitCmpSet(sb, q, "jle", "jg"); break;
            case "==":   emitCmpSet(sb, q, "je", "jne"); break;
            case "!=":   emitCmpSet(sb, q, "jne", "je"); break;
            case "&&":   emitLogical(sb, q, "jne", "jne"); break;
            case "||":   emitLogical(sb, q, "jne", true); break;
            case "J":    sb.append("    jmp  label_").append(q.result).append("\n"); break;
            case "J!=":  emitCondJump(sb, q, "jne"); break;
            case "PARAM": emitPush(sb, q.arg1); break;
            case "CALL": emitCallQuad(sb, q); break;
            case "READ": sb.append("    call _read_int\n");
                         if (!q.result.equals("_")) sb.append("    mov  ").append(q.result).append(", ax\n");
                         break;
            case "write": emitPrint(sb, q.arg1, false); break;
            case "write_str": emitPrint(sb, q.arg2, true); break;
            case "EXIT":
                sb.append("    mov  ah, 4Ch\n");
                sb.append("    int  21h\n");
                break;
        }
    }

    private void emitLabelIfNeeded(StringBuilder sb, int i) {
        if (jumpTargets.contains(i)) {
            sb.append("label_").append(i).append(":\n");
        }
    }

    // ==================== 各指令翻译 ====================

    private void emitAssign(StringBuilder sb, Quad q) {
        String val = resolveValue(q.arg1);
        sb.append("    mov  ax, ").append(val).append("\n");
        sb.append("    mov  ").append(q.result).append(", ax\n");
    }

    private void emitArith(StringBuilder sb, Quad q, String op) {
        String src = resolveValue(q.arg2);
        sb.append("    mov  ax, ").append(resolveValue(q.arg1)).append("\n");
        sb.append("    ").append(op).append("  ax, ").append(src).append("\n");
        sb.append("    mov  ").append(q.result).append(", ax\n");
    }

    private void emitMul(StringBuilder sb, Quad q) {
        sb.append("    mov  ax, ").append(resolveValue(q.arg1)).append("\n");
        sb.append("    mov  bx, ").append(resolveValue(q.arg2)).append("\n");
        sb.append("    imul bx                  ; DX:AX = AX * BX\n");
        sb.append("    mov  ").append(q.result).append(", ax\n");
    }

    private void emitDiv(StringBuilder sb, Quad q, boolean isMod) {
        sb.append("    mov  ax, ").append(resolveValue(q.arg1)).append("\n");
        sb.append("    cwd                      ; 符号扩展 AX → DX:AX\n");
        sb.append("    mov  bx, ").append(resolveValue(q.arg2)).append("\n");
        sb.append("    idiv bx                  ; AX=商, DX=余数\n");
        if (isMod) {
            sb.append("    mov  ").append(q.result).append(", dx\n");
        } else {
            sb.append("    mov  ").append(q.result).append(", ax\n");
        }
    }

    private void emitCmpSet(StringBuilder sb, Quad q, String trueJmp, String falseJmp) {
        String lTrue = "_cs_true_" + (labelCounter);
        String lEnd = "_cs_end_" + (labelCounter);
        labelCounter++;
        sb.append("    mov  ax, ").append(resolveValue(q.arg1)).append("\n");
        sb.append("    cmp  ax, ").append(resolveValue(q.arg2)).append("\n");
        sb.append("    ").append(trueJmp).append("  ").append(lTrue).append("\n");
        sb.append("    mov  ").append(q.result).append(", 0\n");
        sb.append("    jmp  ").append(lEnd).append("\n");
        sb.append(lTrue).append(":\n");
        sb.append("    mov  ").append(q.result).append(", 1\n");
        sb.append(lEnd).append(":\n");
    }

    private void emitLogical(StringBuilder sb, Quad q, String jneOp, boolean isOr) {
        // isOr == false → &&; isOr == true → ||
        String lTrue = "_log_true_" + labelCounter;
        String lEnd = "_log_end_" + labelCounter;
        labelCounter++;
        sb.append("    mov  ax, ").append(resolveValue(q.arg1)).append("\n");
        sb.append("    cmp  ax, 0\n");
        if (isOr) {
            // ||: 第一个为真即可
            sb.append("    jne  ").append(lTrue).append("\n");
            sb.append("    mov  ax, ").append(resolveValue(q.arg2)).append("\n");
            sb.append("    cmp  ax, 0\n");
            sb.append("    jne  ").append(lTrue).append("\n");
        } else {
            // &&: 第一个为假即假
            sb.append("    je   ").append(lEnd).append("      ; 短路: 第一个就是0\n");
            sb.append("    mov  ax, ").append(resolveValue(q.arg2)).append("\n");
            sb.append("    cmp  ax, 0\n");
            sb.append("    je   ").append(lEnd).append("\n");
        }
        sb.append(lTrue).append(":\n");
        sb.append("    mov  ").append(q.result).append(", 1\n");
        sb.append("    jmp  _log_skip_").append(labelCounter).append("\n");
        sb.append(lEnd).append(":\n");
        sb.append("    mov  ").append(q.result).append(", 0\n");
        sb.append("_log_skip_").append(labelCounter).append(":\n");
        labelCounter++;
    }

    // Overload for || case (different structure)
    private void emitLogical(StringBuilder sb, Quad q, String jneOp, boolean isOr) {
        String lTrue = "_log_true_" + labelCounter;
        String lNext = "_log_next_" + labelCounter;
        String lEnd = "_log_end_" + labelCounter;
        labelCounter++;
        sb.append("    mov  ax, ").append(resolveValue(q.arg1)).append("\n");
        sb.append("    cmp  ax, 0\n");
        if (isOr) {
            sb.append("    jne  ").append(lTrue).append("\n");
            sb.append("    mov  ax, ").append(resolveValue(q.arg2)).append("\n");
            sb.append("    cmp  ax, 0\n");
            sb.append("    jne  ").append(lTrue).append("\n");
            sb.append("    mov  ").append(q.result).append(", 0\n");
            sb.append("    jmp  ").append(lEnd).append("\n");
            sb.append(lTrue).append(":\n");
            sb.append("    mov  ").append(q.result).append(", 1\n");
        } else {
            sb.append("    je   _log_fast_false_").append(labelCounter).append("\n");
            sb.append("    mov  ax, ").append(resolveValue(q.arg2)).append("\n");
            sb.append("    cmp  ax, 0\n");
            sb.append("    je   _log_fast_false_").append(labelCounter).append("\n");
            sb.append("    mov  ").append(q.result).append(", 1\n");
            sb.append("    jmp  ").append(lEnd).append("\n");
            sb.append("_log_fast_false_").append(labelCounter).append(":\n");
            sb.append("    mov  ").append(q.result).append(", 0\n");
        }
        sb.append(lEnd).append(":\n");
    }

    private void emitCondJump(StringBuilder sb, Quad q, String jmpOp) {
        sb.append("    mov  ax, ").append(resolveValue(q.arg1)).append("\n");
        sb.append("    cmp  ax, ").append(resolveValue(q.arg2)).append("\n");
        sb.append("    ").append(jmpOp).append("   label_").append(q.result).append("\n");
    }

    private void emitPush(StringBuilder sb, String arg) {
        String val = resolveValue(arg);
        if (isNumber(arg)) {
            sb.append("    mov  ax, ").append(val).append("\n");
            sb.append("    push ax\n");
        } else {
            sb.append("    push ").append(val).append("\n");
        }
    }

    private void emitCallQuad(StringBuilder sb, Quad q) {
        if (q.arg1.equals("write")) {
            sb.append("    mov  ax, ").append(resolveValue(q.arg2)).append("\n");
            sb.append("    call _write_int\n");
        } else if (q.arg1.equals("write_str")) {
            // write_str 在上层被替换为 write_str 处理，这里不处理
            // 实际调用 write_str 的 arg2 存的是字符串内容
            sb.append("    mov  dx, OFFSET _str_for_call\n");
            sb.append("    mov  ah, 09h\n");
            sb.append("    int  21h\n");
        } else {
            // 用户自定义函数调用
            // 注意: 参数已经通过 PARAM quads push 到栈上
            String funcName = sanitizeName(q.arg1);
            sb.append("    call ").append(funcName).append("\n");
            // 清理栈上的参数 (arg2 是参数个数)
            int paramCount;
            try { paramCount = Integer.parseInt(q.arg2); } catch (NumberFormatException e) { paramCount = 0; }
            if (paramCount > 0) {
                sb.append("    add  sp, ").append(paramCount * 2).append("\n");
            }
            // 保存返回值
            if (!q.result.equals("_")) {
                sb.append("    mov  ").append(q.result).append(", ax\n");
            }
        }
    }

    private void emitPrint(StringBuilder sb, String arg, boolean isStr) {
        if (isStr) {
            String cleaned = arg.replace("'", "").replace("\"", "");
            // 如果包含 \n 或 换行，我们需要输出后换行
            if (cleaned.equals("\\n") || cleaned.contains("换行")) {
                sb.append("    mov  dx, OFFSET _newline\n");
                sb.append("    mov  ah, 09h\n");
                sb.append("    int  21h\n");
            } else {
                // 查找或创建字符串常量
                int strIdx = findStringIndex(arg);
                sb.append("    mov  dx, OFFSET _str").append(strIdx).append("\n");
                sb.append("    mov  ah, 09h\n");
                sb.append("    int  21h\n");
            }
        } else {
            sb.append("    mov  ax, ").append(resolveValue(arg)).append("\n");
            sb.append("    call _write_int\n");
        }
    }

    // ==================== 辅助方法 ====================

    private String resolveValue(String s) {
        if (s == null || s.equals("_")) return "0";
        try {
            Integer.parseInt(s);
            return s; // 立即数直接返回
        } catch (NumberFormatException ignored) {}
        return s; // 变量名
    }

    private boolean isNumber(String s) {
        if (s == null || s.isEmpty() || s.equals("_")) return false;
        try { Integer.parseInt(s); return true; } catch (NumberFormatException e) { return false; }
    }

    private String loadToAX(String src) {
        if (isNumber(src)) return src;
        return src; // 用 mov ax, srcName 即可（MASM 会当作内存操作数）
    }

    private int findStringIndex(String s) {
        int idx = 0;
        for (String str : stringLiterals) {
            if (str.equals(s)) return idx;
            idx++;
        }
        return 0;
    }
}
