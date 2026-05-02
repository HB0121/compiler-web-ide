package com.huangbin.campushelperbackend.controller;

import com.huangbin.campushelperbackend.dto.AiParsedTaskDTO;
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

    // 阶段一：仅做 AI 解析
    @PostMapping("/parse")
    public ResponseEntity<?> parseTask(@RequestBody Map<String, String> request) {
        if (request.getText() == null || request.getText().trim().isEmpty()) {
            return ResponseEntity.badRequest().body("输入内容不能为空");
        }

        // 调用 AI 服务提取结构化数据
        AiParsedTaskDTO parsedData = taskAiService.parseUserIntent(request.getText());

        // 组装返回给前端的数据结构 (与前端 Vue 里的 response.data.ai_parsed_data 对应)
        return ResponseEntity.ok().body(Map.of("ai_parsed_data", parsedData));
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