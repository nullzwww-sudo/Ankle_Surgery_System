package com.ankle.backend.controller;

import com.ankle.backend.common.Result;
import com.ankle.backend.entity.PatientInfo;
import com.ankle.backend.service.PatientService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/patient")
public class PatientController {

    @Autowired
    private PatientService patientService;

    // 新增患者接口
    @PostMapping("/add")
    public Result<String> addPatient(@RequestBody PatientInfo patientInfo) {
        try {
            patientService.addPatient(patientInfo);
            return Result.success("患者录入成功！");
        } catch (Exception e) {
            return Result.error(500, e.getMessage());
        }
    }
}