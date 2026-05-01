package com.huangbin.campushelperbackend.controller;

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

    // 阶段一：仅做 AI 解析 (之前写好的)
    @PostMapping("/parse")
    public ResponseEntity<?> parseTask(@RequestBody Map<String, String> request) {
        // ... (之前调用 taskAiService 的代码保持不变)
    }

    // 阶段二：前端确认表单后，正式提交落库
    @PostMapping("/publish")
    public ResponseEntity<?> publishTask(@RequestBody TaskPublishRequest request) {
        if (request.getRawContent() == null || request.getAiParsedData() == null) {
            return ResponseEntity.badRequest().body("任务内容或解析数据不能为空");
        }

        boolean success = taskService.createAndPublishTask(request);
        if (success) {
            return ResponseEntity.ok(Map.of("message", "任务发布成功！"));
        } else {
            return ResponseEntity.internalServerError().body("服务器开小差了，发布失败");
        }
    }
}