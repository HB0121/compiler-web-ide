package com.huangbin.campushelperbackend.controller;

import com.huangbin.campushelperbackend.utils.JwtUtils;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/user")
public class UserController {

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> loginData) {
        String username = loginData.get("username");
        String password = loginData.get("password");

        // 【模拟数据库账号校验】
        // 真实项目中，这里应该去调 UserService 查数据库里的 users 表
        Long userId = null;
        if ("zhangsan".equals(username) && "123456".equals(password)) {
            userId = 1L; // 张三（模拟发单人）
        } else if ("lisi".equals(username) && "123456".equals(password)) {
            userId = 2L; // 李四（模拟接单人）
        }

        if (userId != null) {
            // 校验成功，启动印钞机，颁发 JWT 门票！
            String token = JwtUtils.generateToken(userId);

            return ResponseEntity.ok(Map.of(
                    "code", 200,
                    "message", "登录成功",
                    "data", Map.of(
                            "token", token,      // 把门票给前端
                            "userId", userId,
                            "username", username
                    )
            ));
        } else {
            return ResponseEntity.badRequest().body(Map.of("error", "用户名或密码错误"));
        }
    }
}