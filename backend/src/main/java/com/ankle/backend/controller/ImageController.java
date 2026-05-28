package com.ankle.backend.controller;

import com.ankle.backend.common.Result;
import com.ankle.backend.entity.MedicalImage;
import com.ankle.backend.service.ImageUploadService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/image")
public class ImageController {

    @Autowired
    private ImageUploadService imageUploadService;

    // 接收文件的接口
    @PostMapping("/upload")
    public Result<MedicalImage> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam("patientId") Long patientId,
            @RequestParam("caseId") Long caseId,
            @RequestParam("doctorId") Long doctorId,
            @RequestParam("position") String position) {
        
        try {
            // 调用 Service 保存文件
            MedicalImage savedImage = imageUploadService.uploadImage(file, patientId, caseId, doctorId, position);
            return Result.success(savedImage);
        } catch (Exception e) {
            e.printStackTrace();
            return Result.error(500, "文件上传失败：" + e.getMessage());
        }
    }
}