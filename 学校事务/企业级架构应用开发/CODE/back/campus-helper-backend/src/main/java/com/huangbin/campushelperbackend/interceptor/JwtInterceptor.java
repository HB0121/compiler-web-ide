package com.huangbin.campushelperbackend.interceptor;

import com.huangbin.campushelperbackend.utils.JwtUtils;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class JwtInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 1. 放行 OPTIONS 请求 (浏览器在发跨域的 POST 请求前，会先发一个 OPTIONS 预检请求)
        if ("OPTIONS".equals(request.getMethod())) {
            return true;
        }

        // 2. 从请求头获取 Authorization 字段
        String authHeader = request.getHeader("Authorization");

        // 3. 检查有没有带门票，或者格式对不对 (必须以 Bearer 开头)
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setCharacterEncoding("UTF-8");
            response.getWriter().write("{\"error\": \"未登录或门票无效，请重新登录\"}");
            return false; // 拦截，不准进入 Controller
        }

        // 4. 提取真正的 token 字符串 (去掉前面的 "Bearer " 7个字符)
        String token = authHeader.substring(7);

        try {
            // 5. 使用我们的 JwtUtils 验票，并取出 userId
            Long userId = JwtUtils.getUserIdFromToken(token);

            // 6. 【核心】把真实的用户ID存进 request 里，这样后面的 Controller 就能直接拿到了！
            request.setAttribute("userId", userId);

            return true; // 验票通过，放行！
        } catch (Exception e) {
            // 验票失败（比如伪造的、过期的）
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setCharacterEncoding("UTF-8");
            response.getWriter().write("{\"error\": \"登录已过期，请重新登录\"}");
            return false;
        }
    }
}