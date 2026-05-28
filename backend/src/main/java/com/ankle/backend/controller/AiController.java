package com.ankle.backend.controller;

import com.ankle.backend.common.Result;
import com.ankle.backend.dto.ConfirmKeypointsRequestDTO;
import com.ankle.backend.service.AiIntegrationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api/ai")
public class AiController {

    @Autowired
    private AiIntegrationService aiIntegrationService;

    /**
     * 阶段一：AI 探路 (AOA分期 + 关键点初步检测)
     * 前端传入裁剪后的图像，后端调用算法a和算法b前半部分
     * 返回 AOA 分期结果和 AI 预测的关键点坐标（供前端渲染和医生微调）
     */
    @PostMapping("/detect-keypoints")
    public Result<Map<String, Object>> detectKeypoints(
            @RequestParam("caseId") Long caseId,
            @RequestParam("imageId") Long imageId,
            @RequestParam(value = "cropImage1", required = false) MultipartFile cropImage1,
            @RequestParam(value = "cropImage2", required = false) MultipartFile cropImage2) {
        
        // 调用服务层，只做检测，不出最终方案
        Map<String, Object> detectResult = aiIntegrationService.detectAndReturnKeypoints(caseId, imageId, cropImage1, cropImage2);
        return Result.success(detectResult);
    }

    /**
     * 阶段二：人工确认并生成规划 (角度计算 + 大模型方案)
     * 前端医生微调关键点并点击“确认”后，将最终坐标传回
     * 后端保存坐标、调用算法b后半部分计算角度、调用算法c生成方案
     */
    @PostMapping("/confirm-and-plan")
    public Result<Map<String, Object>> confirmAndPlan(@RequestBody ConfirmKeypointsRequestDTO requestDTO) {
        // 调用服务层，落库人工标注坐标，计算角度，并请求大模型
        Map<String, Object> planResult = aiIntegrationService.confirmPointsAndGeneratePlan(requestDTO);
        return Result.success(planResult);
    }
}