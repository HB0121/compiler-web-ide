package com.huangbin.campushelperbackend.controller;

import com.huangbin.campushelperbackend.dto.TaskParseRequest;
import com.huangbin.campushelperbackend.dto.TaskPublishRequest;
import com.huangbin.campushelperbackend.service.TaskAiService;
import com.huangbin.campushelperbackend.service.TaskService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final TaskAiService taskAiService;
    private final TaskService taskService;

    public TaskController(TaskAiService taskAiService, TaskService taskService) {
        this.taskAiService = taskAiService;
        this.taskService = taskService;
    }

    // 阶段一：AI 解析接口
    @PostMapping("/parse")
    public ResponseEntity<?> parseTask(@RequestBody TaskParseRequest request) { // 这里一定要用 TaskParseRequest 对象
        // 既然 request 是一个对象，就可以使用 getText() 方法了
        if (request.getText() == null || request.getText().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "输入内容不能为空"));
        }

        try {
            // 调用 AI 服务提取结构化数据
            // 注意：这里调用的方法名以你实际在 TaskAiService 中写的为准，之前演示的是 parseUserIntent
            var parsedData = taskAiService.parseUserIntent(request.getText());

            // 返回给前端，与 Vue 中的 response.data.ai_parsed_data 对应
            return ResponseEntity.ok().body(Map.of("ai_parsed_data", parsedData));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", "AI 解析失败"));
        }
    }

    // 阶段二：前端确认表单后，正式提交落库 (保持刚才写的代码即可)
    @PostMapping("/publish")
    public ResponseEntity<?> publishTask(@RequestBody TaskPublishRequest request) {

        // 1. 现在我们只要求前端必须传大白话文本
        if (request.getRawContent() == null || request.getRawContent().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "任务内容不能为空"));
        }

        try {
            // 2. 【核心黑科技】在存入数据库前，后端主动呼叫大模型进行解析！
            var parsedData = taskAiService.parseUserIntent(request.getRawContent());

            // 3. 把大模型辛苦提取出的 JSON 数据，悄悄塞进 request 对象里
            request.setAiParsedData(parsedData);

            // 4. 数据完整了，交给 Service 去保存进 MySQL
            boolean success = taskService.createAndPublishTask(request);

            if (success) {
                return ResponseEntity.ok(Map.of("message", "任务发布成功！"));
            } else {
                return ResponseEntity.internalServerError().body(Map.of("error", "服务器开小差了，发布失败"));
            }
        } catch (Exception e) {
            // 打印错误日志，方便排查
            e.printStackTrace();
            return ResponseEntity.internalServerError().body(Map.of("error", "AI 解析或落库失败：" + e.getMessage()));
        }
    }
}