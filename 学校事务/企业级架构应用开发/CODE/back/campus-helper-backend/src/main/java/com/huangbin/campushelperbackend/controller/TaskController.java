package com.huangbin.campushelperbackend.controller;

import com.huangbin.campushelperbackend.dto.TaskParseRequest;
import com.huangbin.campushelperbackend.dto.TaskPublishRequest;
import com.huangbin.campushelperbackend.service.TaskAiService;
import com.huangbin.campushelperbackend.service.TaskService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final TaskAiService taskAiService;
    private final TaskService taskService;

    public TaskController(TaskAiService taskAiService, TaskService taskService) {
        this.taskAiService = taskAiService;
        this.taskService = taskService;
    }

    // 阶段一：纯粹的 AI 解析接口 (前端边打字边预览解析结果)
    @PostMapping("/parse")
    public ResponseEntity<?> parseTask(@RequestBody TaskParseRequest request) {
        if (request.getText() == null || request.getText().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "输入内容不能为空"));
        }
        try {
            // 这里不需要任何判断，直接干活！
            var parsedData = taskAiService.parseUserIntent(request.getText());
            return ResponseEntity.ok().body(Map.of("ai_parsed_data", parsedData));
        } catch (Exception e) {
            log.error("阶段一 AI 解析失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "AI 解析失败"));
        }
    }

    // 阶段二：智能发布接口 (尊重前端修改，兜底盲发逻辑)
    @PostMapping("/publish")
    public ResponseEntity<?> publishTask(@RequestBody TaskPublishRequest request) {

        if (request.getRawContent() == null || request.getRawContent().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "任务内容不能为空"));
        }

        try {
            // 【核心修复：判断移到了这里】
            // 如果前端传来的 request 里没有 aiParsedData (说明是盲发)，后端才主动呼叫大模型
            if (request.getAiParsedData() == null) {
                var parsedData = taskAiService.parseUserIntent(request.getRawContent());
                request.setAiParsedData(parsedData);
            }
            // 如果有，就直接用前端传来的、用户手动修改确认过的数据，不再重复调 AI 啦！

            // 落库保存
            boolean success = taskService.createAndPublishTask(request);

            if (success) {
                return ResponseEntity.ok(Map.of("message", "任务发布成功！"));
            } else {
                return ResponseEntity.internalServerError().body(Map.of("error", "服务器开小差了，发布失败"));
            }
        } catch (Exception e) {
            log.error("AI 解析或落库失败，原始输入内容: {}", request.getRawContent(), e);
            return ResponseEntity.internalServerError().body(Map.of("error", "业务处理失败：" + e.getMessage()));
        }
    }
}