package com.huangbin.campushelperbackend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.huangbin.campushelperbackend.entity.Task;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TaskMapper extends BaseMapper<Task> {
}
