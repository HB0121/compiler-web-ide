package com.huangbin.campushelperbackend.utils;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import java.util.Date;

public class JwtUtils {

    // 绝密公章：企业级项目中这个秘钥应该放在 application.yml 中，绝对不能泄露
    private static final String SECRET = "CampusHelper_Super_Secret_Key_2026";
    // 过期时间：7天 (单位是毫秒)
    private static final long EXPIRE_TIME = 7 * 24 * 60 * 60 * 1000L;

    /**
     * 1. 制造门票：根据 userId 生成 Token
     */
    public static String generateToken(Long userId) {
        Date now = new Date();
        Date expireDate = new Date(now.getTime() + EXPIRE_TIME);

        return JWT.create()
                .withClaim("userId", userId) // 核心：把 userId 像盖钢印一样塞进门票里
                .withExpiresAt(expireDate)   // 设置过期时间
                .sign(Algorithm.HMAC256(SECRET)); // 用绝密公章加密防伪
    }

    /**
     * 2. 检验门票：验证 Token 并取出 userId (咱们下一步写拦截器时会用到)
     */
    public static Long getUserIdFromToken(String token) {
        return JWT.require(Algorithm.HMAC256(SECRET))
                .build()
                .verify(token) // 如果门票被篡改或已过期，这里会直接抛出异常
                .getClaim("userId").asLong(); // 如果是真的，就把里面的 userId 拿出来
    }
}