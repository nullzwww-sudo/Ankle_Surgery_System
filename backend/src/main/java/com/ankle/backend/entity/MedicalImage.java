package com.ankle.backend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("medical_image")
public class MedicalImage {
    
    @TableId(type = IdType.AUTO)
    private Long imageId;
    
    private Long caseId;           // 关联病例ID
    private Long patientId;        // 关联患者ID
    private String imageFormat;    // 格式(PNG/JPEG/DICOM)
    private String imageResolution;// 分辨率
    private String shootingPosition;// 拍摄体位
    private Long fileSize;         // 文件大小(字节)
    private String storagePath;    // 存储在我们电脑硬盘上的实际路径
    private LocalDateTime uploadTime;
    private Long uploadBy;         // 上传的医生ID
    private Integer isValid;       // 1-有效
}