package com.ankle.backend.service;

import com.ankle.backend.entity.PatientInfo;
import com.ankle.backend.mapper.PatientInfoMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class PatientService {

    @Autowired
    private PatientInfoMapper patientInfoMapper;

    // 添加新患者
    public void addPatient(PatientInfo patientInfo) {
        // 1. 检查病历号是否已经存在 (数据库里要求病历号必须唯一)
        QueryWrapper<PatientInfo> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("medical_record_no", patientInfo.getMedicalRecordNo());
        if (patientInfoMapper.exists(queryWrapper)) {
            throw new RuntimeException("该病历号已存在，无法重复录入！");
        }

        // 2. 补全系统时间
        patientInfo.setCreateTime(LocalDateTime.now());
        patientInfo.setUpdateTime(LocalDateTime.now());
        
        // （如果在真实环境，这里还会把 phone 和 address 进行 AES 加密，契合你的论文要求，
        //   为了方便我们第一次测试跑通，我们先直接存明文，之后可以加）

        // 3. 插入数据库
        patientInfoMapper.insert(patientInfo);
    }
}