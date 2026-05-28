package com.ankle.backend.dto;

import java.util.List;
import lombok.Data;

@Data
public class ConfirmKeypointsRequestDTO {
    private Long caseId;         // 病例ID
    private Long imageId;        // 影像ID
    private Long patientId;      // 患者ID
    private List<PointDTO> keypoints; // 医生微调后确认的关键点列表
}