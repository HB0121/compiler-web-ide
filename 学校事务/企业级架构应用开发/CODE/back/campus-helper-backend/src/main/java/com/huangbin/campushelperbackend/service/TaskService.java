package com.huangbin.campushelperbackend.service;

import com.huangbin.campushelperbackend.dto.TaskPublishRequest;
import com.huangbin.campushelperbackend.entity.Task;
import com.huangbin.campushelperbackend.mapper.TaskMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

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

        // 核心：直接将 Map 赋值给实体，MyBatis-Plus 的 JacksonTypeHandler 会自动把它转成 JSON 存入 MySQL
        task.setAiParsedData(request.getAiParsedData());

        // 2. 提取报酬金额 (从 AI 解析的 Map 中安全提取)
        Object rewardObj = request.getAiParsedData().get("reward");
        BigDecimal reward = BigDecimal.ZERO;
        if (rewardObj != null) {
            reward = new BigDecimal(rewardObj.toString());
        }
        task.setRewardAmount(reward);

        // 3. 设置初始状态：0-待接单
        task.setStatus(0);

        // 4. 执行插入
        int rows = taskMapper.insert(task);
        return rows > 0;
    }
}
