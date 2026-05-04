package com.huangbin.campushelperbackend.controller;

import com.huangbin.campushelperbackend.entity.User;
import com.huangbin.campushelperbackend.service.UserService;
import com.huangbin.campushelperbackend.utils.JwtUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/user")
public class UserController {

    @Autowired
    private UserService userService;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> loginData) {
        // 前端传来的 username，实际上就是我们的 student_id
        String studentId = loginData.get("username");
        String password = loginData.get("password");

        User user = userService.login(studentId, password);

        if (user != null) {
            String token = JwtUtils.generateToken(user.getUserId());

            return ResponseEntity.ok(Map.of(
                    "code", 200,
                    "message", "登录成功",
                    "data", Map.of(
                            "token", token,
                            "userId", user.getUserId(),
                            // 前端展示名字时，我们返回数据库里的 nickname
                            "username", user.getNickname()
                    )
            ));
        } else {
            return ResponseEntity.badRequest().body(Map.of("error", "学号或密码错误"));
        }
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody Map<String, String> registerData) {
        String studentId = registerData.get("studentId");
        String nickname = registerData.get("nickname");
        String password = registerData.get("password");

        if (studentId == null || password == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "学号或密码不能为空"));
        }

        boolean success = userService.register(studentId, nickname, password);

        if (success) {
            return ResponseEntity.ok(Map.of("code", 200, "message", "注册成功！快去登录吧"));
        } else {
            return ResponseEntity.badRequest().body(Map.of("error", "该学号已被注册"));
        }
    }
}