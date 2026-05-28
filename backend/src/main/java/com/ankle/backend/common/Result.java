package com.ankle.backend.common;

import lombok.Data;

/**
 * 统一的接口返回结果封装类
 */
@Data // 这个注解来自于 Lombok，它会自动帮我们写 get/set 方法
public class Result<T> {
    
    private Integer code; // 状态码：200代表成功，500代表失败
    private String message; // 提示信息
    private T data; // 真正要返回的数据内容

    // 成功时的快捷方法
    public static <T> Result<T> success(T data) {
        Result<T> result = new Result<>();
        result.setCode(200);
        result.setMessage("操作成功");
        result.setData(data);
        return result;
    }

    // 成功但不带数据的快捷方法
    public static <T> Result<T> success() {
        return success(null);
    }

    // 失败时的快捷方法
    public static <T> Result<T> error(Integer code, String message) {
        Result<T> result = new Result<>();
        result.setCode(code);
        result.setMessage(message);
        return result;
    }
}