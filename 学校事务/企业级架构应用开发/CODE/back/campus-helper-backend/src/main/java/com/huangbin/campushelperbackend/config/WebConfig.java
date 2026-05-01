package com.huangbin.campushelperbackend.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**") // 拦截所有的接口路径
                // 允许跨域的源。Spring Boot 3 推荐使用 allowedOriginPatterns 而不是 allowedOrigins
                .allowedOriginPatterns("*") // 允许任何前端地址（如 http://localhost:5173）发起请求
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD") // 允许的 HTTP 方法
                .allowedHeaders("*") // 允许前端请求头携带任何参数（后续传 Token 非常关键）
                .allowCredentials(true) // 允许前端携带 Cookie/跨域凭证
                .maxAge(3600); // OPTIONS 预检请求的缓存时间（单位：秒），避免频繁发送 OPTIONS 请求
    }
}
