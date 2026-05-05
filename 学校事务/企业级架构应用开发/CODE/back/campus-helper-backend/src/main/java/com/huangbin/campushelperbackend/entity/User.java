package com.huangbin.campushelperbackend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;

@Data
@TableName("users")
public class User {
    @TableId(type = IdType.AUTO)
    private Long userId;

    private String studentId; // 对应 student_id

    private String nickname;  // 对应 nickname

    private String passwordHash; // 对应 password_hash

    private Integer creditScore; // 对应 credit_score

    private BigDecimal balance;
}