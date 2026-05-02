package com.huangbin.campushelperbackend.service;

import com.huangbin.campushelperbackend.dto.AiParsedTaskDTO; // 确保导入了你的强类型 DTO
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
}