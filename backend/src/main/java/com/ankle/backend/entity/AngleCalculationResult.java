package com.ankle.backend.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class AngleCalculationResult {
    private Long angleId;
    private Long stageId;
    private Long caseId;
    private Long imageId;
    private BigDecimal tasAngle;
    private BigDecimal ttsAngle;
    private BigDecimal ttdApMm;
    private String resultImagePath; // 我们之前新加的字段，存渲染图路径
    private String otherAngle;
    private BigDecimal calculationError;
    private String algorithmVersion;
    private LocalDateTime processTime;
}