package com.huangbin.campushelperbackend.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.huangbin.campushelperbackend.dto.AiParsedTaskDTO; // 确保导入了你的强类型 DTO
import com.huangbin.campushelperbackend.dto.TaskPublishRequest;
import com.huangbin.campushelperbackend.entity.Task;
import com.huangbin.campushelperbackend.mapper.TaskMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

@Service
public class TaskService {

    private final TaskMapper taskMapper;

    public TaskService(TaskMapper taskMapper) {
        this.taskMapper = taskMapper;
    }

    @Transactional(rollbackFor = Exception.class)
    public boolean createAndPublishTask(TaskPublishRequest request) {
        // 1. 组装数据库实体
        Task task = new Task();

        // 实际开发中，发布者ID应该从登录态(如JWT Token)中获取，这里为了跑通流程先用前端传的或写死测试
        task.setPublisherId(request.getPublisherId() != null ? request.getPublisherId() : 1L);
        task.setRawContent(request.getRawContent());

        // 获取我们已经变成强类型 DTO 的解析数据
        AiParsedTaskDTO parsedData = request.getAiParsedData();

        // 核心：将强类型对象赋值给实体
        task.setAiParsedData(parsedData);

        // 2. 提取报酬金额 【核心修改：用 getter 方法代替 .get("reward")】
        BigDecimal reward = BigDecimal.ZERO;
        if (parsedData != null && parsedData.getReward() != null) {
            // 安全转换：无论 DTO 里 reward 是 Double 还是 Integer，先转成 String 再给 BigDecimal，不会丢精度
            reward = new BigDecimal(parsedData.getReward().toString());
        }
        task.setRewardAmount(reward);

        // 3. 设置初始状态 【修正类型隐患：因为实体类里 status 是 String，这里加上双引号】
        task.setStatus("0"); // "0" 代表待接单

        // 4. 执行插入
        int rows = taskMapper.insert(task);
        return rows > 0;
    }

    /**
     * 获取任务大厅的可用任务列表
     */
    public List<Task> getAvailableTasks() {
        // 使用 MyBatis-Plus 的 Lambda 构造器，极其优雅且能防止字段名拼写错误
        LambdaQueryWrapper<Task> wrapper = new LambdaQueryWrapper<>();

        // 核心查询条件：
        // 1. 只查状态为 "0"（待接单）的任务
        // 2. 按照 TaskId 倒序排列（最新的任务在最上面展示）
        wrapper.eq(Task::getStatus, "0")
                .orderByDesc(Task::getTaskId);

        return taskMapper.selectList(wrapper);
    }

    /**
     * 【升级版】抢单逻辑：不仅改状态，还要记录是谁接的单
     */
    public boolean grabTask(Long taskId, Long receiverId) {
        LambdaUpdateWrapper<Task> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.eq(Task::getTaskId, taskId)
                .eq(Task::getStatus, "0")
                .set(Task::getStatus, "1")
                .set(Task::getReceiverId, receiverId); // 核心：记录下接单人的 ID

        return taskMapper.update(null, updateWrapper) > 0;
    }

    /**
     * 确认完成逻辑：状态从 1 改为 2 (已完成)
     */
    public boolean completeTask(Long taskId, Long publisherId) {
        LambdaUpdateWrapper<Task> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.eq(Task::getTaskId, taskId)
                .eq(Task::getPublisherId, publisherId) // 核心防范：确保只有发单人能确认
                .eq(Task::getStatus, "1") // 只有“进行中”的任务才能确认
                .set(Task::getStatus, "2"); // "2" 代表已完成

        return taskMapper.update(null, updateWrapper) > 0;
    }

    /**
     * 查询：我发布的任务
     */
    public List<Task> getMyPublishedTasks(Long publisherId) {
        LambdaQueryWrapper<Task> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Task::getPublisherId, publisherId)
                .orderByDesc(Task::getTaskId); // 依然是最新的在最前面
        return taskMapper.selectList(wrapper);
    }

    /**
     * 查询：我接到的任务
     */
    public List<Task> getMyGrabbedTasks(Long receiverId) {
        LambdaQueryWrapper<Task> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Task::getReceiverId, receiverId)
                .orderByDesc(Task::getTaskId);
        return taskMapper.selectList(wrapper);
    }


}