package com.ankle.backend.dto;

import lombok.Data;

@Data // 自动生成 get/set
public class LoginDTO {
    private String username;
    private String password;
}