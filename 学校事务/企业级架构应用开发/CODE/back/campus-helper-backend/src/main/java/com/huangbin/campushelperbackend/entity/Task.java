package com.huangbin.campushelperbackend.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import com.huangbin.campushelperbackend.dto.AiParsedTaskDTO;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Map;

@Data
@TableName(value = "tasks", autoResultMap = true) // autoResultMap 必须开启，为了支持复杂的 JSON 类型转换
public class Task {

    @TableId(type = IdType.AUTO)
    private Long taskId;

    private Long publisherId;

    private Long accepterId;

    private String rawContent;

    // 【核心亮点】：自动将 MySQL 的 JSON 转为 Java 的 Map 或自定义 DTO 对象
    @TableField(typeHandler = JacksonTypeHandler.class)
    private AiParsedTaskDTO aiParsedData;

    private BigDecimal rewardAmount;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    /**
     * 接单人 ID
     */
    private Long receiverId;
}
