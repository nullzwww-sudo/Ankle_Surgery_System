package com.ankle.backend.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class ImageAnnotation {
    private Long annotationId;
    private Long imageId;
    private Long caseId;
    private String landmarkName;
    private BigDecimal xCoordinate;
    private BigDecimal yCoordinate;
    private Integer annotationType; // 1-AI自动标注, 2-人工标注
    private Long annotationBy; // 关联 sys_user
    private LocalDateTime annotationTime;
    private String remark;
}