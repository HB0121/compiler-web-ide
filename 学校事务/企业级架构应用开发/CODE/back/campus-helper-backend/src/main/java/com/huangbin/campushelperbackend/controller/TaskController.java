package com.huangbin.campushelperbackend.controller;

import com.huangbin.campushelperbackend.dto.TaskParseRequest;
import com.huangbin.campushelperbackend.dto.TaskPublishRequest;
import com.huangbin.campushelperbackend.service.TaskAiService;
import com.huangbin.campushelperbackend.service.TaskService;
import lombok.extern.slf4j.Slf4j; // 引入日志模块
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@Slf4j  // 第一步：加上这个强大的日志注解
@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final TaskAiService taskAiService;
    private final TaskService taskService;

    public TaskController(TaskAiService taskAiService, TaskService taskService) {
        this.taskAiService = taskAiService;
        this.taskService = taskService;
    }

    // 阶段一：保留，供前端边打字边预览解析结果（可选）
    @PostMapping("/parse")
    public ResponseEntity<?> parseTask(@RequestBody TaskParseRequest request) {
        if (request.getText() == null || request.getText().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "输入内容不能为空"));
        }
        try {
            if (request.getAiParsedData() == null) {
                var parsedData = taskAiService.parseUserIntent(request.getText());
                return ResponseEntity.ok().body(Map.of("ai_parsed_data", parsedData));
            }
        } catch (Exception e) {
            log.error("阶段一 AI 解析失败", e); // 使用 log.error
            return ResponseEntity.internalServerError().body(Map.of("error", "AI 解析失败"));
        }
    }

    // 阶段二：一键全自动发布落库
    @PostMapping("/publish")
    public ResponseEntity<?> publishTask(@RequestBody TaskPublishRequest request) {

        if (request.getRawContent() == null || request.getRawContent().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "任务内容不能为空"));
        }

        try {
            // 1. 呼叫大模型解析纯文本
            var parsedData = taskAiService.parseUserIntent(request.getRawContent());

            // 2. 将强类型的 DTO 塞回 request (刚才修改了 TaskPublishRequest 后，这里就不会报错了)
            request.setAiParsedData(parsedData);

            // 3. 落库保存
            boolean success = taskService.createAndPublishTask(request);

            if (success) {
                return ResponseEntity.ok(Map.of("message", "任务发布成功！"));
            } else {
                return ResponseEntity.internalServerError().body(Map.of("error", "服务器开小差了，发布失败"));
            }
        } catch (Exception e) {
            // 第二步：使用企业级日志记录错误！这不仅规范，而且能在控制台打印出漂亮的红色高亮日志
            log.error("AI 解析或落库失败，原始输入内容: {}", request.getRawContent(), e);
            return ResponseEntity.internalServerError().body(Map.of("error", "业务处理失败：" + e.getMessage()));
        }
    }
}