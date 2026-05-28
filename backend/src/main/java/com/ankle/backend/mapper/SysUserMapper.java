package com.ankle.backend.mapper;

import com.ankle.backend.entity.SysUser;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;

@Mapper // 加上这个注解，Spring 启动时就能找到它，刚才的警告就消失了！
public interface SysUserMapper extends BaseMapper<SysUser> {
    // 继承了 BaseMapper，我们就直接拥有了查询、插入、删除等功能
}