package com.huangbin.compiler.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Token {
    private String text;
    private int code;
    private int line;
    private int column = 1;
    private String kind = "";
}