package com.huangbin.campushelperbackend.controller;

import com.huangbin.campushelperbackend.dto.TaskParseRequest;
import com.huangbin.campushelperbackend.dto.TaskPublishRequest;
import com.huangbin.campushelperbackend.entity.Task;
import com.huangbin.campushelperbackend.service.TaskAiService;
import com.huangbin.campushelperbackend.service.TaskService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    @Autowired
    private TaskAiService taskAiService;

    @Autowired
    private TaskService taskService;

    // ==========================================
    // 1. AI 解析接口 (原汁原味的找回版)
    // ==========================================
    @PostMapping("/parse")
    public ResponseEntity<?> parseTask(@RequestBody TaskParseRequest request) {
        if (request.getText() == null || request.getText().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "输入内容不能为空"));
        }
        try {
            var parsedData = taskAiService.parseUserIntent(request.getText());
            // 注意：Vite前端如果要求 code 状态码，可以像下面这样包一层，更加规范
            return ResponseEntity.ok().body(Map.of("ai_parsed_data", parsedData));
        } catch (Exception e) {
            log.error("阶段一 AI 解析失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "AI 解析失败"));
        }
    }

    // ==========================================
    // 2. 智能发布接口 (AI盲发 + JWT鉴权结合)
    // ==========================================
    @PostMapping("/publish")
    public ResponseEntity<?> publishTask(@RequestBody TaskPublishRequest request, HttpServletRequest servletRequest) {
        if (request.getRawContent() == null || request.getRawContent().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "任务内容不能为空"));
        }

        try {
            // 【核心融合点】：从安检门里拿出真实的 userId！
            Long currentUserId = (Long) servletRequest.getAttribute("userId");

            // 💡 提示：你的 TaskPublishRequest DTO 类里需要有 publisherId 字段
            // 如果你之前没写，记得去 DTO 里加一下，不然这里会报错
            request.setPublisherId(currentUserId);

            // AI 兜底解析逻辑
            if (request.getAiParsedData() == null) {
                var parsedData = taskAiService.parseUserIntent(request.getRawContent());
                request.setAiParsedData(parsedData);
            }

            // 落库保存
            boolean success = taskService.createAndPublishTask(request);

            if (success) {
                return ResponseEntity.ok(Map.of("code", 200, "message", "任务发布成功！"));
            } else {
                return ResponseEntity.badRequest().body(Map.of("error", "服务器开小差了，发布失败"));
            }
        } catch (Exception e) {
            log.error("业务处理失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "业务处理失败：" + e.getMessage()));
        }
    }

    // ==========================================
    // 3. 任务大厅列表
    // ==========================================
    @GetMapping("/list")
    public ResponseEntity<?> getTaskList() {
        try {
            List<Task> list = taskService.getAvailableTasks();
            return ResponseEntity.ok(Map.of("code", 200, "data", list));
        } catch (Exception e) {
            log.error("查询列表失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "获取列表失败"));
        }
    }

    // ==========================================
    // 4. 抢单接口
    // ==========================================
    @PostMapping("/grab/{taskId}")
    public ResponseEntity<?> grabTask(@PathVariable Long taskId, HttpServletRequest request) {
        try {
            Long currentUserId = (Long) request.getAttribute("userId");
            boolean success = taskService.grabTask(taskId, currentUserId);
            if (success) {
                return ResponseEntity.ok(Map.of("code", 200, "message", "抢单成功！"));
            } else {
                return ResponseEntity.badRequest().body(Map.of("error", "手慢了，已被抢走！"));
            }
        } catch (Exception e) {
            log.error("抢单异常", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "服务器异常"));
        }
    }

    // ==========================================
    // 5. 我发布的 / 我接单的
    // ==========================================
    @GetMapping("/my-published")
    public ResponseEntity<?> getMyPublished(HttpServletRequest request) {
        try {
            Long currentUserId = (Long) request.getAttribute("userId");
            List<Task> list = taskService.getMyPublishedTasks(currentUserId);
            return ResponseEntity.ok(Map.of("code", 200, "data", list));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", "查询失败"));
        }
    }

    @GetMapping("/my-grabbed")
    public ResponseEntity<?> getMyGrabbed(HttpServletRequest request) {
        try {
            Long currentUserId = (Long) request.getAttribute("userId");
            List<Task> list = taskService.getMyGrabbedTasks(currentUserId);
            return ResponseEntity.ok(Map.of("code", 200, "data", list));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", "查询失败"));
        }
    }

    // ==========================================
    // 6. 确认完成并评价结算 (带事务)
    // ==========================================
    @PostMapping("/complete/{taskId}")
    public ResponseEntity<?> completeTask(@PathVariable Long taskId, @RequestBody Map<String, Object> payload, HttpServletRequest request) {
        try {
            Long currentUserId = (Long) request.getAttribute("userId");
            Integer rating = (Integer) payload.getOrDefault("rating", 5);
            String comment = (String) payload.getOrDefault("comment", "默认好评！");

            boolean success = taskService.completeTaskWithReview(taskId, currentUserId, rating, comment);

            if (success) {
                return ResponseEntity.ok(Map.of("code", 200, "message", "结算成功！"));
            } else {
                return ResponseEntity.badRequest().body(Map.of("error", "操作失败"));
            }
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", "服务器异常"));
        }
    }
}