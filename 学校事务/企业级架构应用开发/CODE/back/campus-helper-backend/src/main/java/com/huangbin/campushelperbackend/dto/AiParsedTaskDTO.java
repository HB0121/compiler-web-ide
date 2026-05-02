package com.huangbin.campushelperbackend.dto;

import java.util.List;

/**
 * 映射大模型返回的JSON
 */
public class AiParsedTaskDTO {
    private String time;
    private String location;
    private String action;
    private Double reward;
    private List<String> tags;
    // getter/setter 省略
}
