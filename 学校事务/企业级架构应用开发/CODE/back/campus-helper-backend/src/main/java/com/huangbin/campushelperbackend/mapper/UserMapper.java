package com.huangbin.campushelperbackend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.huangbin.campushelperbackend.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 继承 BaseMapper，直接拥有 CRUD 超能力！
}