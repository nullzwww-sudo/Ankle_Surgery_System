package com.ankle.backend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data // Lombok 注解，自动生成 get/set 方法
@TableName("sys_user") // 告诉系统这个类对应数据库的 sys_user 表
public class SysUser {
    
    // @TableId 告诉系统这是主键，IdType.AUTO 表示自增
    @TableId(type = IdType.AUTO)
    private Long userId;
    
    private String username;
    private String password;
    private String realName;
    private String department;
    private String title;
    private Integer roleId;
    private Integer status;
    private String phone;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    private LocalDateTime lastLoginTime;
}