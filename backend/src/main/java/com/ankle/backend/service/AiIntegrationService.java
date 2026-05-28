package com.ankle.backend.service;

import cn.hutool.http.HttpRequest;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.ankle.backend.dto.ConfirmKeypointsRequestDTO;
import com.ankle.backend.dto.PointDTO;
import com.ankle.backend.entity.AoaStageResult;
import com.ankle.backend.entity.ImageAnnotation;
import com.ankle.backend.entity.AngleCalculationResult;
import com.ankle.backend.entity.SurgicalPlan;
import com.ankle.backend.mapper.AoaStageResultMapper;
import com.ankle.backend.mapper.ImageAnnotationMapper;
import com.ankle.backend.mapper.AngleCalculationResultMapper;
import com.ankle.backend.mapper.SurgicalPlanMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AiIntegrationService {

    @Autowired
    private AoaStageResultMapper aoaStageResultMapper;

    // 【解开注释】注入刚刚创建的三个 Mapper
    @Autowired 
    private ImageAnnotationMapper imageAnnotationMapper;
    
    @Autowired 
    private AngleCalculationResultMapper angleCalculationResultMapper;
    
    @Autowired 
    private SurgicalPlanMapper surgicalPlanMapper;

    private static final String PYTHON_AI_BASE_URL = "http://localhost:8000/api/ai";

    /**
     * 阶段一：AI 探路 (双图上传 -> AOA分期 + 关键点初步检测)
     */
    public Map<String, Object> detectAndReturnKeypoints(Long caseId, Long imageId, MultipartFile cropImage1, MultipartFile cropImage2) {
        Map<String, Object> responseMap = new HashMap<>();
        System.out.println("1. [Java端阶段一] 收到前端裁剪图像，准备呼叫 Python AI 进行探路...");

        File tempFile1 = null;
        File tempFile2 = null;
        try {
            if (cropImage1 != null && !cropImage1.isEmpty()) {
                tempFile1 = File.createTempFile("crop1_", ".png");
                cropImage1.transferTo(tempFile1);
            }
            if (cropImage2 != null && !cropImage2.isEmpty()) {
                tempFile2 = File.createTempFile("crop2_", ".png");
                cropImage2.transferTo(tempFile2);
            }

            String targetUrl = PYTHON_AI_BASE_URL + "/detect_stage_and_points";
            HttpRequest request = HttpRequest.post(targetUrl).timeout(30000);
            request.form("case_id", caseId);
            request.form("image_id", imageId);
            if (tempFile1 != null) request.form("crop1", tempFile1);
            if (tempFile2 != null) request.form("crop2", tempFile2);

            String responseBody = request.execute().body();
            System.out.println("2. [Java端阶段一] 收到 Python 探路结果: " + responseBody);

            JSONObject resultJson = JSONUtil.parseObj(responseBody);
            if (resultJson.getInt("code") == 200) {
                JSONObject data = resultJson.getJSONObject("data");
                
                AoaStageResult resultObj = new AoaStageResult();
                resultObj.setCaseId(caseId);
                resultObj.setImageId(imageId);
                resultObj.setPatientId(data.getLong("patient_id", 0L));
                resultObj.setAoaStage(data.getStr("aoa_stage"));
                resultObj.setStageBasis(data.getStr("stage_basis"));
                resultObj.setAlgorithmVersion(data.getStr("algorithm_version", "v1.0"));
                resultObj.setErrorRange(data.getBigDecimal("error_range", new java.math.BigDecimal("0.0")));
                resultObj.setProcessTime(LocalDateTime.now());
                resultObj.setProcessStatus(1);
                aoaStageResultMapper.insert(resultObj);
                
                responseMap.put("status", "success");
                responseMap.put("aoaStage", data.getStr("aoa_stage"));
                responseMap.put("stageBasis", data.getStr("stage_basis"));
                responseMap.put("keypoints", data.getJSONArray("keypoints"));
            } else {
                responseMap.put("status", "error");
                responseMap.put("message", "AI 算法处理异常");
            }

        } catch (Exception e) {
            e.printStackTrace();
            responseMap.put("status", "error");
            responseMap.put("message", "调用探路算法异常：" + e.getMessage());
        } finally {
            if (tempFile1 != null && tempFile1.exists()) tempFile1.delete();
            if (tempFile2 != null && tempFile2.exists()) tempFile2.delete();
        }
        return responseMap;
    }

    /**
     * 阶段二：人工确认并生成大模型规划方案
     */
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> confirmPointsAndGeneratePlan(ConfirmKeypointsRequestDTO requestDTO) {
        Map<String, Object> responseMap = new HashMap<>();
        System.out.println("1. [Java端阶段二] 收到医生微调确认的关键点，准备落库并计算角度...");

        try {
            Long caseId = requestDTO.getCaseId();
            // 查出阶段一保存的记录，获取外键所需的 stageId 和 patientId
            AoaStageResult latestStage = aoaStageResultMapper.selectLatestByCaseId(caseId);
            if (latestStage == null) {
                throw new RuntimeException("找不到该病例对应的 AOA 分期记录，请先执行阶段一。");
            }

            // 【落库逻辑 1】：保存医生手动微调后的 6 个关键点坐标到 image_annotation 表
            List<PointDTO> points = requestDTO.getKeypoints();
            if (points != null) {
                for (int i = 0; i < points.size(); i++) {
                    PointDTO pt = points.get(i);
                    ImageAnnotation annotation = new ImageAnnotation();
                    annotation.setImageId(latestStage.getImageId());
                    annotation.setCaseId(caseId);
                    annotation.setLandmarkName("P" + (i + 1)); // P1 到 P6
                    annotation.setXCoordinate(BigDecimal.valueOf(pt.getX()));
                    annotation.setYCoordinate(BigDecimal.valueOf(pt.getY()));
                    annotation.setAnnotationType(2); // 2 代表医生人工微调修改后的坐标
                    annotation.setAnnotationBy(1L);  // 默认当前操作医师用户 ID 为 1
                    annotation.setAnnotationTime(LocalDateTime.now());
                    annotation.setRemark("医生前端微调确认点");
                    imageAnnotationMapper.insert(annotation);
                }
            }

            // 发送给 Python AI 计算角度与提取轮廓
            String calcUrl = PYTHON_AI_BASE_URL + "/calculate_angles";
            String calcResponse = HttpRequest.post(calcUrl)
                    .body(JSONUtil.toJsonStr(requestDTO))
                    .timeout(20000)
                    .execute().body();
            
            JSONObject calcResult = JSONUtil.parseObj(calcResponse);
            if (calcResult.getInt("code") != 200) throw new RuntimeException("算法角度计算失败");

            JSONObject calcData = calcResult.getJSONObject("data");
            Double tas = calcData.getDouble("tas_angle");
            Double tts = calcData.getDouble("tts_angle");
            Double ttd = calcData.getDouble("TTD_AP_mm"); 
            String finalImgPath = calcData.getStr("final_image_path");

            // 【落库逻辑 2】：将 Python 计算出的 TAS、TTS、TTD 角度距离结果保存到 angle_calculation_result 表
            AngleCalculationResult angleRes = new AngleCalculationResult();
            angleRes.setStageId(latestStage.getStageId());
            angleRes.setCaseId(caseId);
            angleRes.setImageId(latestStage.getImageId());
            angleRes.setTasAngle(BigDecimal.valueOf(tas));
            angleRes.setTtsAngle(BigDecimal.valueOf(tts));
            angleRes.setTtdApMm(BigDecimal.valueOf(ttd));
            angleRes.setResultImagePath(finalImgPath); // 存放带标注渲染图的 URL
            angleRes.setCalculationError(BigDecimal.valueOf(0.0));
            angleRes.setAlgorithmVersion("v1.0");
            angleRes.setProcessTime(LocalDateTime.now());
            angleRes.setOtherAngle("{}");
            angleCalculationResultMapper.insert(angleRes); // 插入后，MyBatis 会自动将自增主键注入到 angleRes.getAngleId() 中

            System.out.println("2. [Java端阶段二] 角度计算完毕，请求大模型出方案...");
            String planUrl = PYTHON_AI_BASE_URL + "/generate_plan";
            JSONObject planRequest = new JSONObject();
            planRequest.set("tas", tas);
            planRequest.set("tts", tts);
            planRequest.set("ttd", ttd);
            planRequest.set("case_id", caseId);

            String planResponse = HttpRequest.post(planUrl)
                    .body(planRequest.toString())
                    .timeout(60000) 
                    .execute().body();

            JSONObject planResult = JSONUtil.parseObj(planResponse);
            if (planResult.getInt("code") != 200) throw new RuntimeException("大模型方案生成失败");

            String planContent = planResult.getJSONObject("data").getStr("plan_content");

            // 【落库逻辑 3】：将大模型生成的方案报告保存到 surgical_plan 表
            SurgicalPlan plan = new SurgicalPlan();
            plan.setAngleId(angleRes.getAngleId()); // 关联刚才生成的角度结果主键
            plan.setCaseId(caseId);
            plan.setPatientId(latestStage.getPatientId());
            plan.setOsteotomyPosition("胫骨远端"); // 默认初筛位置
            plan.setOsteotomyAngle(BigDecimal.ZERO);
            plan.setDistractionHeight(BigDecimal.ZERO);
            plan.setFixationMethod("内固定钢板建议");
            plan.setModelPath3d("暂无");
            plan.setPlanStatus(0); // 0 代表草稿
            plan.setAdjustRecord(planContent); // 存储大模型返回的文本报告
            plan.setCreateTime(LocalDateTime.now());
            plan.setUpdateTime(LocalDateTime.now());
            surgicalPlanMapper.insert(plan);

            responseMap.put("status", "success");
            responseMap.put("angles", Map.of("TAS", tas, "TTS", tts, "TTD", ttd));
            responseMap.put("finalImagePath", finalImgPath);
            responseMap.put("surgicalPlanReport", planContent);

        } catch (Exception e) {
            e.printStackTrace();
            responseMap.put("status", "error");
            responseMap.put("message", "生成规划失败: " + e.getMessage());
            throw new RuntimeException(e);
        }

        return responseMap;
    }
}
