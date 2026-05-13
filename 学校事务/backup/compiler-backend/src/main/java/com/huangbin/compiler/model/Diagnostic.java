package com.huangbin.compiler.model;

/** @author 黄彬 (12303070250) */

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Diagnostic {
    private String phase;   // 所处阶段，如 "lexer", "parser", "semantic"
    private int line;       // 错误行号
    private String code;    // 错误代码，如 "SEM302"
    private String message; // 详细错误信息

    public String format() {
        return String.format("%d %s %s: %s", line, code, phase, message);
    }
}