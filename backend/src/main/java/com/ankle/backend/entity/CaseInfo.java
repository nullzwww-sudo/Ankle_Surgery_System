package com.ankle.backend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("case_info")
public class CaseInfo {
    
    @TableId(type = IdType.AUTO)
    private Long caseId;
    
    private Long patientId;     // 关联的患者ID (外键)
    private String caseName;    // 病例名称
    private Integer caseStatus; // 状态: 0-未完成, 1-已完成, 2-已存档
    private Long createBy;      // 创建医生ID
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    private String remark;      // 备注说明
}