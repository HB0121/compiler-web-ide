package com.huangbin.campushelperbackend.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.huangbin.campushelperbackend.entity.User;
import com.huangbin.campushelperbackend.mapper.UserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.DigestUtils;

@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    /**
     * 登录：通过学号和哈希密码校验
     */
    public User login(String studentId, String rawPassword) {
        // 把前端传来的明文密码 (如 123456) 转换成 MD5 哈希值
        String md5Password = DigestUtils.md5DigestAsHex(rawPassword.getBytes());

        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(User::getStudentId, studentId)
                .eq(User::getPasswordHash, md5Password);

        return userMapper.selectOne(wrapper);
    }

    /**
     * 注册：新增用户并加密密码
     */
    public boolean register(String studentId, String nickname, String rawPassword) {
        // 1. 检查学号是否已存在
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(User::getStudentId, studentId);
        if (userMapper.selectCount(wrapper) > 0) {
            return false; // 学号已被注册
        }

        // 2. 加密密码
        String md5Password = DigestUtils.md5DigestAsHex(rawPassword.getBytes());

        // 3. 插入新用户
        User newUser = new User();
        newUser.setStudentId(studentId);
        newUser.setNickname(nickname);
        newUser.setPasswordHash(md5Password);
        newUser.setCreditScore(100); // 默认 100 分

        return userMapper.insert(newUser) > 0;
    }
}