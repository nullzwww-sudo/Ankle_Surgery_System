package com.ankle.backend.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class SurgicalPlan {
    private Long planId;
    private Long angleId;
    private Long caseId;
    private Long patientId;
    private String osteotomyPosition;
    private BigDecimal osteotomyAngle;
    private BigDecimal distractionHeight;
    private String fixationMethod;
    private String modelPath3d; // 对应 3d_model_path
    private Integer planStatus; // 0-草稿, 1-已确认, 2-已废弃
    private String adjustRecord; // 这里我们可以用来存大模型返回的文本建议
    private Long confirmBy;
    private LocalDateTime confirmTime;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}