package com.huangbin.compiler.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.ArrayList;
import java.util.List;

@Data
@NoArgsConstructor
public class ASTNode {
    private String name;
    private Integer line;
    private String value;
    private List<ASTNode> children = new ArrayList<>();

    public ASTNode(String name) {
        this.name = name;
    }

    public void addChild(ASTNode child) {
        if (child != null) {
            this.children.add(child);
        }
    }
}