package com.huangbin.campushelperbackend.dto;

import lombok.Data;

import java.util.List;

/**
 * 映射大模型返回的JSON
 */
@Data
public class AiParsedTaskDTO {
    private String time;
    private String location;
    private String action;
    private Double reward;
    private List<String> tags;
    // getter/setter 省略
}
