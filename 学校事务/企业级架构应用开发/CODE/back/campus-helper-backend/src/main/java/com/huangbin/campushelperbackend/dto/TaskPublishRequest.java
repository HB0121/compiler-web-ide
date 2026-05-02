package com.huangbin.campushelperbackend.dto;

import lombok.Data;

import java.util.Map;

@Data
public class TaskPublishRequest {
    // 假设当前操作的用户ID，后期可以从 Token 中获取
    private Long publisherId;

    // 用户输入的原始一句话
    private String rawContent;

    // 前端表单确认后的结构化数据 (时间、地点、动作、报酬等)
    private AiParsedTaskDTO aiParsedData;
}
