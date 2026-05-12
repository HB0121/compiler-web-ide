package com.huangbin.compiler.model;

import lombok.Data;

@Data
public class CompileRequest {
    private String sourceCode; // 接收前端传来的源代码
}