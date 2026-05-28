package com.ankle.backend.service;

import cn.hutool.crypto.digest.BCrypt;
import cn.hutool.jwt.JWT;
import com.ankle.backend.entity.SysUser;
import com.ankle.backend.mapper.SysUserMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SysUserService {

    @Autowired
    private SysUserMapper sysUserMapper;

    // 之前写的查询所有用户
    public List<SysUser> getAllUsers() {
        return sysUserMapper.selectList(null);
    }

    // ========== 新增：登录逻辑 ==========
    public String login(String username, String password) {
        // 1. 去数据库里找这个账号
        QueryWrapper<SysUser> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("username", username);
        SysUser user = sysUserMapper.selectOne(queryWrapper);

        if (user == null) {
            throw new RuntimeException("账号不存在！");
        }

        // 2. 校验密码 (用 BCrypt 算法比对前端传的明文和数据库里的密文)
        if (!BCrypt.checkpw(password, user.getPassword())) {
            throw new RuntimeException("密码错误！");
        }

        if (user.getStatus() == 0) {
            throw new RuntimeException("该账号已被禁用！");
        }

        // 3. 密码正确，签发 JWT Token (就相当于给医生发了一张带芯片的门禁卡)
        String token = JWT.create()
                .setPayload("userId", user.getUserId())
                .setPayload("username", user.getUsername())
                .setPayload("roleId", user.getRoleId())
                .setKey("AnkleSurgerySecretKey2026".getBytes()) // 这是咱们服务器的私钥，随便设但不能泄露
                .sign();

        return token;
    }
}