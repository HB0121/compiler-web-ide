package com.huangbin.compiler.model;

/** @author 黄彬 (12303070250) */

import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class CompileResult {
    private List<Token> tokens;
    private ASTNode ast;
    private List<Diagnostic> diagnostics;
    private List<String> quads;             // 格式化后的四元式字符串列表
    private List<String> interpreterOutput; // 中间代码解释器的运行结果
    private String assemblyCode;           // MASM 16-bit 汇编代码
    private String llvmIR;                 // LLVM IR 代码 (选做 4.2)
    private Map<String, Object> compileLog; // 编译流水线日志 (选做 4.1)
    private Map<String, Object> cfgAnalysis; // 控制流图 + DAG 优化结果 (选做 4.4)

    // 如果整体运行成功（没有阻塞型错误）则为 true
    private boolean success;
}