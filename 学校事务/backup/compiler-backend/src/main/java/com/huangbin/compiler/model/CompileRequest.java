package com.huangbin.compiler.model;

/** @author 黄彬 (12303070250) */

import lombok.Data;

@Data
public class CompileRequest {
    private String sourceCode; // 接收前端传来的源代码
}