package com.huangbin.campushelperbackend.config;

import com.huangbin.campushelperbackend.interceptor.JwtInterceptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    // 注入我们刚刚写好的 JWT 安检门
    @Autowired
    private JwtInterceptor jwtInterceptor;

    // ================== 1. 跨域配置 (保持你原有的不变) ==================
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**") // 拦截所有的接口路径
                .allowedOriginPatterns("*") // 允许任何前端地址发起请求
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD") // 允许的 HTTP 方法
                .allowedHeaders("*") // 允许前端请求头携带任何参数（后续传 Token 非常关键）
                .allowCredentials(true) // 允许前端携带 Cookie/跨域凭证
                .maxAge(3600); // OPTIONS 预检请求的缓存时间
    }

    // ================== 2. 拦截器配置 (新增) ==================
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(jwtInterceptor)
                .addPathPatterns("/api/**") // 拦截所有 /api 开头的请求
                .excludePathPatterns("/api/user/login"); // 唯独放行登录接口（不然怎么拿门票呢？）
    }
}