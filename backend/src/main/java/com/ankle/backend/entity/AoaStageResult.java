package com.ankle.backend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("aoa_stage_result")
public class AoaStageResult {
    
    @TableId(type = IdType.AUTO)
    private Long stageId;
    
    private Long caseId;
    private Long imageId;
    private Long patientId;
    
    private String aoaStage;          // AOA 分期结果
    private String stageBasis;        // 分期依据
    private String algorithmVersion;  // 算法版本
    private BigDecimal errorRange;    // 误差范围
    
    private LocalDateTime processTime;// 处理时间
    private Integer processStatus;    // 状态: 1-成功, 0-失败
}