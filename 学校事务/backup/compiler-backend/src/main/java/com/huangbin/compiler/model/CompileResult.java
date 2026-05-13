package com.huangbin.compiler.model;

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

    // 如果整体运行成功（没有阻塞型错误）则为 true
    private boolean success;
}