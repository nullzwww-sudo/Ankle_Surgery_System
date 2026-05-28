package com.ankle.backend.controller;

import com.ankle.backend.common.Result;
import com.ankle.backend.entity.CaseInfo;
import com.ankle.backend.service.CaseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/case")
public class CaseController {

    @Autowired
    private CaseService caseService;

    // 创建病例接口
    @PostMapping("/add")
    public Result<String> addCase(@RequestBody CaseInfo caseInfo) {
        try {
            caseService.addCase(caseInfo);
            return Result.success("病例创建成功！");
        } catch (Exception e) {
            return Result.error(500, e.getMessage());
        }
    }
}