package com.huangbin.campushelperbackend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("reviews")
public class Review {
    @TableId(type = IdType.AUTO)
    private Long reviewId;
    private Long taskId;
    private Long reviewerId;
    private Long revieweeId;
    private Integer rating;
    private String comment;
}