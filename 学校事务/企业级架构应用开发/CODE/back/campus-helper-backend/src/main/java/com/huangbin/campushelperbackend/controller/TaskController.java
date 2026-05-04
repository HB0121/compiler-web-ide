package com.huangbin.campushelperbackend.controller;

import com.huangbin.campushelperbackend.dto.TaskParseRequest;
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
    private TaskService taskService;

    @Autowired
    private TaskAiService taskAiService;


    @PostMapping("/parse")
    public ResponseEntity<?> parseTask(@RequestBody TaskParseRequest request) {
        if (request.getText() == null || request.getText().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "输入内容不能为空"));
        }
        try {
            var parsedData = taskAiService.parseUserIntent(request.getText());
            return ResponseEntity.ok().body(Map.of("ai_parsed_data", parsedData));
        } catch (Exception e) {
            log.error("阶段一 AI 解析失败", e); // 使用 log.error
            return ResponseEntity.internalServerError().body(Map.of("error", "AI 解析失败"));
        }
    }

    // ==========================================
    // 1. 发布任务接口
    // ==========================================
    @PostMapping("/publish")
    public ResponseEntity<?> publishTask(@RequestBody Task task, HttpServletRequest request) {
        try {
            // 【核心鉴权】从拦截器放入的 request 中取出真实身份
            Long currentUserId = (Long) request.getAttribute("userId");

            task.setPublisherId(currentUserId); // 设置发单人 ID
            task.setStatus("0"); // 初始状态为 0 (待接单)

            // 调用 MyBatis-Plus 默认的 save 方法保存到数据库
            boolean success = taskService.saveTask(task);

            if (success) {
                return ResponseEntity.ok(Map.of("code", 200, "message", "任务发布成功！"));
            } else {
                return ResponseEntity.badRequest().body(Map.of("error", "发布失败，请稍后再试"));
            }
        } catch (Exception e) {
            log.error("发布任务异常", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "服务器开小差了"));
        }
    }

    // ==========================================
    // 2. 获取任务大厅列表 (查询所有 status="0" 的任务)
    // ==========================================
    @GetMapping("/list")
    public ResponseEntity<?> getTaskList() {
        try {
            // 提示：这个接口如果在你那边有单独写 SQL 或者 Wrapper 查询，请换成你的方法名
            // 这里假设你的 TaskService 里有一个查 available 的方法，或者直接用 LambdaQueryWrapper 查 status="0"
            List<Task> list = taskService.getAvailableTasks();
            return ResponseEntity.ok(Map.of("code", 200, "data", list));
        } catch (Exception e) {
            log.error("查询任务列表失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "获取列表失败"));
        }
    }

    // ==========================================
    // 3. 抢单接口
    // ==========================================
    @PostMapping("/grab/{taskId}")
    public ResponseEntity<?> grabTask(@PathVariable Long taskId, HttpServletRequest request) {
        try {
            // 取出真实的接单人身份
            Long currentUserId = (Long) request.getAttribute("userId");

            boolean success = taskService.grabTask(taskId, currentUserId);

            if (success) {
                return ResponseEntity.ok(Map.of("message", "抢单成功！快去联系发布者吧！", "code", 200));
            } else {
                return ResponseEntity.badRequest().body(Map.of("error", "手慢了，该任务已被抢走或不存在！"));
            }
        } catch (Exception e) {
            log.error("抢单异常，任务ID: {}", taskId, e);
            return ResponseEntity.internalServerError().body(Map.of("error", "服务器开小差了，抢单失败"));
        }
    }

    // ==========================================
    // 4. 获取“我发布的”任务列表
    // ==========================================
    @GetMapping("/my-published")
    public ResponseEntity<?> getMyPublished(HttpServletRequest request) {
        try {
            // 取出真实的身份
            Long currentUserId = (Long) request.getAttribute("userId");

            List<Task> list = taskService.getMyPublishedTasks(currentUserId);
            return ResponseEntity.ok(Map.of("code", 200, "data", list));
        } catch (Exception e) {
            log.error("查询我发布的任务失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "查询失败"));
        }
    }

    // ==========================================
    // 5. 获取“我接单的”任务列表
    // ==========================================
    @GetMapping("/my-grabbed")
    public ResponseEntity<?> getMyGrabbed(HttpServletRequest request) {
        try {
            // 取出真实的身份
            Long currentUserId = (Long) request.getAttribute("userId");

            List<Task> list = taskService.getMyGrabbedTasks(currentUserId);
            return ResponseEntity.ok(Map.of("code", 200, "data", list));
        } catch (Exception e) {
            log.error("查询我接到的任务失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "查询失败"));
        }
    }

    // ==========================================
    // 6. 确认完成任务 (带评价与信用分结算)
    // ==========================================
    @PostMapping("/complete/{taskId}")
    public ResponseEntity<?> completeTask(
            @PathVariable Long taskId,
            @RequestBody Map<String, Object> payload,
            HttpServletRequest request) {
        try {
            Long currentUserId = (Long) request.getAttribute("userId");

            // 从前端传来的 payload 中提取星星数和评价文字，做一下防空处理
            Integer rating = (Integer) payload.getOrDefault("rating", 5);
            String comment = (String) payload.getOrDefault("comment", "默认好评！");

            boolean success = taskService.completeTaskWithReview(taskId, currentUserId, rating, comment);

            if (success) {
                return ResponseEntity.ok(Map.of("code", 200, "message", "任务已确认完成，评价已提交！"));
            } else {
                return ResponseEntity.badRequest().body(Map.of("error", "操作失败：任务状态异常或您无权操作"));
            }
        } catch (Exception e) {
            log.error("确认完成异常", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "服务器开小差了"));
        }
    }
}