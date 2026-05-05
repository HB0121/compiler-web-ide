package com.huangbin.campushelperbackend.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.huangbin.campushelperbackend.dto.AiParsedTaskDTO; // 确保导入了你的强类型 DTO
import com.huangbin.campushelperbackend.dto.TaskPublishRequest;
import com.huangbin.campushelperbackend.entity.Review;
import com.huangbin.campushelperbackend.entity.Task;
import com.huangbin.campushelperbackend.entity.User;
import com.huangbin.campushelperbackend.mapper.ReviewMapper;
import com.huangbin.campushelperbackend.mapper.TaskMapper;
import com.huangbin.campushelperbackend.mapper.UserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

@Service
public class TaskService {

    private final TaskMapper taskMapper;

    @Autowired
    private ReviewMapper reviewMapper;
    @Autowired
    private UserMapper userMapper;

    public TaskService(TaskMapper taskMapper) {
        this.taskMapper = taskMapper;
    }

    // ==========================================
    // 1. 发单方法 (带扣款验证)
    // ==========================================
    @Transactional(rollbackFor = Exception.class)
    public boolean createAndPublishTask(TaskPublishRequest request) {
        // 1. 组装数据库实体
        Task task = new Task();

        // 实际开发中，发布者ID应该从登录态获取
        task.setPublisherId(request.getPublisherId() != null ? request.getPublisherId() : 1L);
        task.setRawContent(request.getRawContent());

        // 获取解析数据并赋值
        AiParsedTaskDTO parsedData = request.getAiParsedData();
        task.setAiParsedData(parsedData);

        // 2. 提取报酬金额
        BigDecimal reward = BigDecimal.ZERO;
        if (parsedData != null && parsedData.getReward() != null) {
            reward = new BigDecimal(parsedData.getReward().toString());
        }
        task.setRewardAmount(reward);

        // 3. 设置初始状态
        task.setStatus("0"); // "0" 代表待接单

        // ================= 核心修改：资金扣减逻辑 =================
        // 3.1 查出发单人的钱包 (调用 userMapper)
        User publisher = userMapper.selectById(task.getPublisherId());
        if (publisher == null) {
            throw new RuntimeException("找不到发单用户信息！");
        }

        // 防御性编程：如果历史数据余额为空，给个0
        if (publisher.getBalance() == null) {
            publisher.setBalance(BigDecimal.ZERO);
        }

        // 3.2 检查余额够不够 (compareTo: -1表示小于)
        if (publisher.getBalance().compareTo(reward) < 0) {
            throw new RuntimeException("钱包余额不足啦！你的余额只剩: ￥" + publisher.getBalance());
        }

        // 3.3 扣除赏金并更新到数据库
        publisher.setBalance(publisher.getBalance().subtract(reward));
        userMapper.updateById(publisher);
        // ==========================================================

        // 4. 执行插入任务
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

    // ==========================================
    // 2. 结算方法 (带评价与打款)
    // ==========================================
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class) // 开启事务控制，保证数据一致性
    public boolean completeTaskWithReview(Long taskId, Long publisherId, Integer rating, String comment) {
        // 1. 查出任务，确认是不是这个发单人的，且状态必须是 "1"（进行中）
        Task task = taskMapper.selectById(taskId);
        if (task == null || !task.getPublisherId().equals(publisherId) || !"1".equals(task.getStatus())) {
            return false;
        }

        // 2. 更新任务状态为 "2" (已完成)
        task.setStatus("2");
        taskMapper.updateById(task);

        // 3. 写入评价表 (reviews)
        Review review = new Review();
        review.setTaskId(taskId);
        review.setReviewerId(publisherId); // 发单人
        review.setRevieweeId(task.getReceiverId());
        review.setRating(rating);
        review.setComment(comment);
        reviewMapper.insert(review);

        // 4. 动态计算并更新接单人的信用分和钱包
        User reviewee = userMapper.selectById(task.getReceiverId());
        if (reviewee != null) {
            int scoreChange = 0;
            // 奖惩分明：5星加2分，4星加1分，3星不加不减，2星扣2分，1星扣5分
            switch (rating) {
                case 5: scoreChange = 2; break;
                case 4: scoreChange = 1; break;
                case 3: scoreChange = 0; break;
                case 2: scoreChange = -2; break;
                case 1: scoreChange = -5; break;
                default: scoreChange = 0;
            }
            reviewee.setCreditScore(reviewee.getCreditScore() + scoreChange);

            // ================= 核心修改：资金结算打款 =================
            // 防御性编程：如果接单人钱包是空的，给个0
            if (reviewee.getBalance() == null) {
                reviewee.setBalance(BigDecimal.ZERO);
            }
            // 将这笔任务的赏金，打入接单人的余额中
            if (task.getRewardAmount() != null) {
                reviewee.setBalance(reviewee.getBalance().add(task.getRewardAmount()));
            }
            // ==========================================================

            userMapper.updateById(reviewee);
        }

        return true;
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

    /**
     * 新增：保存发布的新任务
     */
    public boolean saveTask(Task task) {
        // 调用 MyBatis-Plus 的 baseMapper 插入数据
        return taskMapper.insert(task) > 0;
    }


}