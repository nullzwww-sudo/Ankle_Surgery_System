package com.ankle.backend.service;

import com.ankle.backend.entity.CaseInfo;
import com.ankle.backend.entity.PatientInfo;
import com.ankle.backend.mapper.CaseInfoMapper;
import com.ankle.backend.mapper.PatientInfoMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class CaseService {

    @Autowired
    private CaseInfoMapper caseInfoMapper;

    @Autowired
    private PatientInfoMapper patientInfoMapper;

    // 创建新病例
    public void addCase(CaseInfo caseInfo) {
        // 1. 校验绑定的患者是否存在
        PatientInfo patient = patientInfoMapper.selectById(caseInfo.getPatientId());
        if (patient == null) {
            throw new RuntimeException("关联的患者不存在，无法创建病例！");
        }

        // 2. 初始化默认值
        caseInfo.setCaseStatus(0); // 默认 0-未完成
        caseInfo.setCreateTime(LocalDateTime.now());
        caseInfo.setUpdateTime(LocalDateTime.now());

        // 3. 插入数据库
        caseInfoMapper.insert(caseInfo);
    }
}