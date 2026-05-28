package com.ankle.backend.controller;

import com.ankle.backend.common.Result;
import com.ankle.backend.dto.LoginDTO;
import com.ankle.backend.entity.SysUser;
import com.ankle.backend.service.SysUserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*; // 注意这里改成星号，引入所有注解
import cn.hutool.crypto.digest.BCrypt;

import java.util.List;

@RestController
@RequestMapping("/user")
public class SysUserController {

    @Autowired
    private SysUserService sysUserService;

    @GetMapping("/list")
    public Result<List<SysUser>> getUserList() {
        return Result.success(sysUserService.getAllUsers());
    }

    // ========== 新增：登录接口 ==========
    // 登录必须用 @PostMapping，因为要把密码藏在请求体里，不能暴露在网址上
    @PostMapping("/login")
    public Result<String> login(@RequestBody LoginDTO loginDTO) {
        try {
            // 调用厨师的登录方法，拿到做好的门禁卡(Token)
            String token = sysUserService.login(loginDTO.getUsername(), loginDTO.getPassword());
            return Result.success(token);
        } catch (Exception e) {
            // 如果账号密码不对，就返回错误信息
            return Result.error(500, e.getMessage());
        }
    }

    // 引入 BCrypt，如果上面没引入的话，确保有这行：
    // import cn.hutool.crypto.digest.BCrypt;

    @GetMapping("/getSecret")
    public Result<String> getSecret() {
        // 让 Hutool 帮我们把 123456 加密，并返回出来
        String secretPwd = BCrypt.hashpw("123456", BCrypt.gensalt());
        return Result.success(secretPwd);
    }
}