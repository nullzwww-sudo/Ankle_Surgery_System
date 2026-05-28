package com.ankle.backend.dto;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class AiResponseDTO {
    private Integer code;
    private String message;
    private AiData data;

    @Data
    public static class AiData {
        // 对应 Python 接口返回的字段
        private String aoa_stage;
        private String stage_basis;
        private String algorithm_version;
        private BigDecimal error_range;
    }
}