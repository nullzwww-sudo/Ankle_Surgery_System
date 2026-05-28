package com.ankle.backend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("patient_info")
public class PatientInfo {
    
    @TableId(type = IdType.AUTO)
    private Long patientId;
    
    private String medicalRecordNo; // 病历号(医院唯一标识)
    private String realName;        // 真实姓名
    private Integer gender;         // 性别:1-男, 2-女, 0-未知
    private Integer age;            // 年龄
    private String diagnosis;       // 临床诊断结果
    private LocalDateTime visitTime;// 就诊时间
    private String phone;           // 手机号
    private String address;         // 住址
    
    private Long createBy;          // 记录创建此患者的医生ID
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}