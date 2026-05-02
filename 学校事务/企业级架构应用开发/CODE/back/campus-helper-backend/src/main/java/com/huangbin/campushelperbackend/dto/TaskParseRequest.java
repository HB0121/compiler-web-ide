package com.huangbin.campushelperbackend.dto;

import lombok.Data;

/**
 * 接收前端信息
 */
@Data
public class TaskParseRequest {
    private Long publisherId;
    private String rawContent;

    // 把原来的 Map<String, Object> 或者 Object 替换成下面这行：
    private AiParsedTaskDTO aiParsedData;
}
