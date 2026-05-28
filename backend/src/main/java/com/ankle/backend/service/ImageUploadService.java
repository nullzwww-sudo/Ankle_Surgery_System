package com.ankle.backend.service;

import com.ankle.backend.entity.MedicalImage;
import com.ankle.backend.mapper.MedicalImageMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class ImageUploadService {

    @Autowired
    private MedicalImageMapper medicalImageMapper;

    // 定义一个你想保存图片的本地硬盘路径 (请确保你的 D 盘有这个文件夹，如果没有程序会自动建)
    private static final String UPLOAD_DIR = "D:/Ankle_Surgery_System/upload_images/";

    public MedicalImage uploadImage(MultipartFile file, Long patientId, Long caseId, Long doctorId, String position) throws IOException {
        
        // 1. 确保目录存在
        File dir = new File(UPLOAD_DIR);
        if (!dir.exists()) {
            dir.mkdirs(); 
        }

        // 2. 生成一个唯一的文件名 (防止多张图片重名覆盖)
        String originalFilename = file.getOriginalFilename();
        String extension = originalFilename.substring(originalFilename.lastIndexOf("."));
        String newFileName = UUID.randomUUID().toString() + extension;
        
        // 3. 把文件真实地存到你的 D 盘
        String fullPath = UPLOAD_DIR + newFileName;
        File dest = new File(fullPath);
        file.transferTo(dest);

        // 4. 把影像信息记录到数据库
        MedicalImage imageRecord = new MedicalImage();
        imageRecord.setCaseId(caseId);
        imageRecord.setPatientId(patientId);
        imageRecord.setImageFormat(extension.replace(".", "").toUpperCase()); // 把 .png 变成 PNG
        imageRecord.setImageResolution("待AI读取"); // 暂填，后续可以由 AI 或图像工具库读取
        imageRecord.setShootingPosition(position);
        imageRecord.setFileSize(file.getSize());
        imageRecord.setStoragePath(fullPath);
        imageRecord.setUploadTime(LocalDateTime.now());
        imageRecord.setUploadBy(doctorId);
        imageRecord.setIsValid(1);

        medicalImageMapper.insert(imageRecord);

        return imageRecord; // 返回保存好的记录
    }
}