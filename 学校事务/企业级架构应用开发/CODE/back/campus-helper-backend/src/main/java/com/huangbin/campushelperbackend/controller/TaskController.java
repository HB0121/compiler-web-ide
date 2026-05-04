package com.huangbin.campushelperbackend.controller;

import com.huangbin.campushelperbackend.dto.TaskParseRequest;
import com.huangbin.campushelperbackend.dto.TaskPublishRequest;
import com.huangbin.campushelperbackend.entity.Task;
import com.huangbin.campushelperbackend.service.TaskAiService;
import com.huangbin.campushelperbackend.service.TaskService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
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

    // 阶段三：任务大厅列表查询接口
    @GetMapping("/list")
    public ResponseEntity<?> getTaskList() {
        try {
            // 去 Service 拿数据
            List<Task> taskList = taskService.getAvailableTasks();

            // 组装标准的企业级 JSON 响应结构返回给前端
            return ResponseEntity.ok(Map.of(
                    "code", 200,
                    "message", "获取任务大厅数据成功",
                    "data", taskList
            ));
        } catch (Exception e) {
            log.error("查询任务列表失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "服务器开小差了，获取数据失败"));
        }
    }

    // 【修改】阶段四：接单/抢单接口 (增加了模拟用户ID)
    @PostMapping("/grab/{taskId}")
    public ResponseEntity<?> grabTask(@PathVariable Long taskId) {
        try {
            Long currentUserId = 2L; // 模拟当前登录的用户是 2 号同学（接单方）
            boolean success = taskService.grabTask(taskId, currentUserId);

            if (success) {
                return ResponseEntity.ok(Map.of("message", "抢单成功！快去联系发布者吧！"));
            } else {
                return ResponseEntity.badRequest().body(Map.of("error", "手慢了，该任务已被抢走或不存在！"));
            }
        } catch (Exception e) {
            log.error("抢单异常，任务ID: {}", taskId, e);
            return ResponseEntity.internalServerError().body(Map.of("error", "服务器开小差了，抢单失败"));
        }
    }

    // ================= 新增：个人订单管理接口 =================

    // 1. 获取我发出的任务列表
    @GetMapping("/my-published")
    public ResponseEntity<?> getMyPublished() {
        try {
            Long currentUserId = 1L; // 模拟当前登录的用户是 1 号同学（发单方）
            List<Task> list = taskService.getMyPublishedTasks(currentUserId);
            return ResponseEntity.ok(Map.of("code", 200, "data", list));
        } catch (Exception e) {
            log.error("查询我发布的任务失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "查询失败"));
        }
    }

    // 2. 获取我接到的任务列表
    @GetMapping("/my-grabbed")
    public ResponseEntity<?> getMyGrabbed() {
        try {
            Long currentUserId = 2L; // 模拟当前登录的用户是 2 号同学（接单方）
            List<Task> list = taskService.getMyGrabbedTasks(currentUserId);
            return ResponseEntity.ok(Map.of("code", 200, "data", list));
        } catch (Exception e) {
            log.error("查询我接到的任务失败", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "查询失败"));
        }
    }

    // 阶段五：确认完成任务（结算）
    @PostMapping("/complete/{taskId}")
    public ResponseEntity<?> completeTask(@PathVariable Long taskId) {
        try {
            Long currentUserId = 1L; // 模拟当前登录的是 1 号同学（发单方）
            boolean success = taskService.completeTask(taskId, currentUserId);

            if (success) {
                return ResponseEntity.ok(Map.of("message", "任务已确认完成，赏金已结算！"));
            } else {
                return ResponseEntity.badRequest().body(Map.of("error", "操作失败：可能任务状态不对或您无权操作"));
            }
        } catch (Exception e) {
            log.error("确认完成异常，任务ID: {}", taskId, e);
            return ResponseEntity.internalServerError().body(Map.of("error", "服务器开小差了"));
        }
    }

}