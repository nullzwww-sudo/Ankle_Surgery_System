-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: ankle_surgery_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `angle_calculation_result`
--

DROP TABLE IF EXISTS `angle_calculation_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `angle_calculation_result` (
  `angle_id` bigint NOT NULL AUTO_INCREMENT COMMENT '角度结果唯一标识 ID',
  `stage_id` bigint NOT NULL COMMENT '关联 AOA 分期结果表(aoa_stage_result)的stage_id',
  `case_id` bigint NOT NULL COMMENT '关联病例表(case_info)的case_id',
  `image_id` bigint NOT NULL COMMENT '关联影像表(medical_image)的image_id',
  `tas_angle` decimal(5,2) NOT NULL COMMENT 'TAS角 / TAS_degree (单位:°)',
  `tts_angle` decimal(5,2) NOT NULL COMMENT 'TTS角 / TTS_degree (单位:°)',
  `ttd_ap_mm` decimal(5,2) NOT NULL COMMENT 'TTD前后距离 / TTD_AP_mm (单位:mm)',
  `result_image_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '算法 b 最终生成的带标注效果图路径',
  `other_angle` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '其他辅助角度参数(JSON格式, 如“内翻角”:8.5)',
  `calculation_error` decimal(5,2) NOT NULL COMMENT '角度计算误差(如“±1.2°”)',
  `algorithm_version` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所用算法版本',
  `process_time` datetime NOT NULL COMMENT '算法处理时间',
  PRIMARY KEY (`angle_id`),
  KEY `fk_angle_stage` (`stage_id`),
  KEY `fk_angle_case` (`case_id`),
  KEY `fk_angle_image` (`image_id`),
  CONSTRAINT `fk_angle_case` FOREIGN KEY (`case_id`) REFERENCES `case_info` (`case_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_angle_image` FOREIGN KEY (`image_id`) REFERENCES `medical_image` (`image_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_angle_stage` FOREIGN KEY (`stage_id`) REFERENCES `aoa_stage_result` (`stage_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角度计算结果表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `aoa_stage_result`
--

DROP TABLE IF EXISTS `aoa_stage_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `aoa_stage_result` (
  `stage_id` bigint NOT NULL AUTO_INCREMENT COMMENT '分期结果唯一标识 ID',
  `case_id` bigint NOT NULL COMMENT '关联病例表(case_info)的case_id',
  `image_id` bigint NOT NULL COMMENT '关联影像表(medical_image)的image_id',
  `patient_id` bigint NOT NULL COMMENT '关联患者表(patient_info)的patient_id',
  `aoa_stage` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'AOA 分期结果(如“Takakura I期”“Takakura IIIb期”)',
  `stage_basis` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分期依据(如“关节间隙狭窄程度<50%, 无骨赘形成”)',
  `algorithm_version` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所用算法版本(如“v1.2.0”)',
  `error_range` decimal(5,2) NOT NULL COMMENT '分期判定误差范围(如“±0.3”)',
  `process_time` datetime NOT NULL COMMENT '算法处理时间',
  `process_status` tinyint NOT NULL COMMENT '处理状态:1-成功, 0-失败',
  PRIMARY KEY (`stage_id`),
  KEY `idx_patient_id` (`patient_id`),
  KEY `idx_process_time` (`process_time`),
  KEY `fk_aoa_case` (`case_id`),
  KEY `fk_aoa_image` (`image_id`),
  CONSTRAINT `fk_aoa_case` FOREIGN KEY (`case_id`) REFERENCES `case_info` (`case_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_aoa_image` FOREIGN KEY (`image_id`) REFERENCES `medical_image` (`image_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_aoa_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient_info` (`patient_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AOA 分期结果表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `case_info`
--

DROP TABLE IF EXISTS `case_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `case_info` (
  `case_id` bigint NOT NULL AUTO_INCREMENT COMMENT '病例唯一标识 ID',
  `patient_id` bigint NOT NULL COMMENT '关联患者表(patient_info)的patient_id',
  `case_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '病例名称(如“20240520-踝上截骨规划-张三”)',
  `case_status` tinyint NOT NULL DEFAULT '0' COMMENT '病例状态:0-未完成, 1-已完成, 2-已存档',
  `create_by` bigint NOT NULL COMMENT '关联用户表(sys_user)的user_id, 记录创建医师 ID',
  `create_time` datetime NOT NULL COMMENT '病例创建时间',
  `update_time` datetime NOT NULL COMMENT '病例最后修改时间',
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '病例备注(如患者特殊情况、手术规划说明)',
  PRIMARY KEY (`case_id`),
  KEY `idx_case_status` (`case_status`),
  KEY `idx_create_by` (`create_by`),
  KEY `fk_case_patient` (`patient_id`),
  CONSTRAINT `fk_case_creator` FOREIGN KEY (`create_by`) REFERENCES `sys_user` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_case_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient_info` (`patient_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='病例表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `image_annotation`
--

DROP TABLE IF EXISTS `image_annotation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `image_annotation` (
  `annotation_id` bigint NOT NULL AUTO_INCREMENT COMMENT '标注唯一标识 ID',
  `image_id` bigint NOT NULL COMMENT '关联影像表(medical_image)的image_id',
  `case_id` bigint NOT NULL COMMENT '关联病例表(case_info)的case_id',
  `landmark_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关键点名称(如“TAS”“TLS”“内踝尖”)',
  `x_coordinate` decimal(10,2) NOT NULL COMMENT '关键点 X 坐标(像素级)',
  `y_coordinate` decimal(10,2) NOT NULL COMMENT '关键点 Y 坐标(像素级)',
  `annotation_type` tinyint NOT NULL COMMENT '标注类型:1-AI自动标注, 2-人工标注',
  `annotation_by` bigint NOT NULL COMMENT '关联用户表(sys_user)的user_id, AI标注时为系统默认ID(0)',
  `annotation_time` datetime NOT NULL COMMENT '标注时间',
  `remark` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '标注备注(如“手动修正关键点位置”)',
  PRIMARY KEY (`annotation_id`),
  KEY `fk_annotation_image` (`image_id`),
  KEY `fk_annotation_case` (`case_id`),
  KEY `fk_annotation_user` (`annotation_by`),
  CONSTRAINT `fk_annotation_case` FOREIGN KEY (`case_id`) REFERENCES `case_info` (`case_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_annotation_image` FOREIGN KEY (`image_id`) REFERENCES `medical_image` (`image_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_annotation_user` FOREIGN KEY (`annotation_by`) REFERENCES `sys_user` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='影像标注表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `medical_image`
--

DROP TABLE IF EXISTS `medical_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medical_image` (
  `image_id` bigint NOT NULL AUTO_INCREMENT COMMENT '影像唯一标识 ID',
  `case_id` bigint NOT NULL COMMENT '关联病例表(case_info)的case_id',
  `patient_id` bigint NOT NULL COMMENT '关联患者表(patient_info)的patient_id',
  `image_format` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '影像格式(如“DICOM”“JPEG”“PNG”)',
  `image_resolution` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '影像分辨率(如“512×512”“1024×1024”)',
  `shooting_position` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '拍摄体位(如“负重位”“非负重位”“侧位”)',
  `file_size` bigint NOT NULL COMMENT '影像文件大小(单位:字节)',
  `storage_path` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '影像文件存储路径',
  `upload_time` datetime NOT NULL COMMENT '影像上传时间',
  `upload_by` bigint NOT NULL COMMENT '关联用户表(sys_user)的user_id, 记录上传医师 ID',
  `is_valid` tinyint NOT NULL DEFAULT '1' COMMENT '影像是否有效:1-有效, 0-无效',
  PRIMARY KEY (`image_id`),
  KEY `idx_patient_id` (`patient_id`),
  KEY `idx_upload_time` (`upload_time`),
  KEY `fk_image_case` (`case_id`),
  KEY `fk_image_uploader` (`upload_by`),
  CONSTRAINT `fk_image_case` FOREIGN KEY (`case_id`) REFERENCES `case_info` (`case_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_image_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient_info` (`patient_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_image_uploader` FOREIGN KEY (`upload_by`) REFERENCES `sys_user` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='影像表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `patient_info`
--

DROP TABLE IF EXISTS `patient_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patient_info` (
  `patient_id` bigint NOT NULL AUTO_INCREMENT COMMENT '患者唯一标识 ID',
  `medical_record_no` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '患者病历号(医院唯一标识)',
  `real_name` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '患者真实姓名',
  `gender` tinyint NOT NULL COMMENT '性别:1-男, 2-女, 0-未知',
  `age` tinyint NOT NULL COMMENT '患者年龄(单位:岁)',
  `diagnosis` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '临床诊断结果(如“内翻型踝关节炎(Takakura III期)”)',
  `visit_time` datetime NOT NULL COMMENT '就诊时间',
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '患者联系电话(脱敏存储)',
  `address` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '患者住址(可选,脱敏存储)',
  `create_by` bigint NOT NULL COMMENT '关联用户表(sys_user)的user_id, 记录创建医师 ID',
  `create_time` datetime NOT NULL COMMENT '患者信息创建时间',
  `update_time` datetime NOT NULL COMMENT '患者信息最后修改时间',
  PRIMARY KEY (`patient_id`),
  UNIQUE KEY `uk_medical_record_no` (`medical_record_no`),
  KEY `idx_visit_time` (`visit_time`),
  KEY `fk_patient_creator` (`create_by`),
  CONSTRAINT `fk_patient_creator` FOREIGN KEY (`create_by`) REFERENCES `sys_user` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='患者表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `surgical_plan`
--

DROP TABLE IF EXISTS `surgical_plan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `surgical_plan` (
  `plan_id` bigint NOT NULL AUTO_INCREMENT COMMENT '方案唯一标识 ID',
  `angle_id` bigint NOT NULL COMMENT '关联角度计算结果表(angle_calculation_result)的angle_id',
  `case_id` bigint NOT NULL COMMENT '关联病例表(case_info)的case_id',
  `patient_id` bigint NOT NULL COMMENT '关联患者表(patient_info)的patient_id',
  `osteotomy_position` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '截骨位置(如“胫骨远端外侧”)',
  `osteotomy_angle` decimal(5,2) NOT NULL COMMENT '截骨角度(单位:°)',
  `distraction_height` decimal(5,2) NOT NULL COMMENT '撑开高度(单位:mm)',
  `fixation_method` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '固定方式建议(如“钢板螺钉固定”“外固定架固定”)',
  `3d_model_path` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '3D 截骨模拟模型存储路径',
  `plan_status` tinyint NOT NULL DEFAULT '0' COMMENT '方案状态:0-草稿, 1-已确认, 2-已废弃',
  `adjust_record` text COLLATE utf8mb4_unicode_ci COMMENT '方案调整记录(JSON格式)',
  `confirm_by` bigint DEFAULT NULL COMMENT '关联用户表(sys_user)的user_id, 记录确认医师ID(方案确认后赋值)',
  `confirm_time` datetime DEFAULT NULL COMMENT '方案确认时间',
  `create_time` datetime NOT NULL COMMENT '方案生成时间',
  `update_time` datetime NOT NULL COMMENT '方案最后修改时间',
  PRIMARY KEY (`plan_id`),
  KEY `fk_plan_angle` (`angle_id`),
  KEY `fk_plan_case` (`case_id`),
  KEY `fk_plan_patient` (`patient_id`),
  KEY `fk_plan_confirmer` (`confirm_by`),
  CONSTRAINT `fk_plan_angle` FOREIGN KEY (`angle_id`) REFERENCES `angle_calculation_result` (`angle_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_plan_case` FOREIGN KEY (`case_id`) REFERENCES `case_info` (`case_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_plan_confirmer` FOREIGN KEY (`confirm_by`) REFERENCES `sys_user` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_plan_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient_info` (`patient_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='术前规划方案表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_config`
--

DROP TABLE IF EXISTS `sys_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_config` (
  `config_id` bigint NOT NULL AUTO_INCREMENT COMMENT '配置唯一标识 ID',
  `config_key` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置键(如“algorithm_aoa_url”“data_backup_cycle”)',
  `config_value` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置值',
  `config_desc` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '配置描述(如“AOA分期算法接口地址”)',
  `update_by` bigint NOT NULL COMMENT '关联用户表(sys_user)的user_id, 记录修改管理员ID',
  `update_time` datetime NOT NULL COMMENT '配置最后修改时间',
  PRIMARY KEY (`config_id`),
  UNIQUE KEY `uk_config_key` (`config_key`),
  KEY `fk_config_updater` (`update_by`),
  CONSTRAINT `fk_config_updater` FOREIGN KEY (`update_by`) REFERENCES `sys_user` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_operation_log`
--

DROP TABLE IF EXISTS `sys_operation_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_operation_log` (
  `log_id` bigint NOT NULL AUTO_INCREMENT COMMENT '日志唯一标识 ID',
  `user_id` bigint NOT NULL COMMENT '关联用户表(sys_user)的user_id',
  `operation_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作类型(如“登录”“影像上传”“规划方案生成”“病例导出”)',
  `operation_content` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作内容(如“上传患者张三DICOM影像10张”)',
  `operation_ip` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作IP 地址',
  `operation_result` tinyint NOT NULL COMMENT '操作结果:1-成功, 0-失败',
  `operation_time` datetime NOT NULL COMMENT '操作时间',
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作备注(如“导出失败:权限不足”)',
  PRIMARY KEY (`log_id`),
  KEY `fk_log_user` (`user_id`),
  CONSTRAINT `fk_log_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_permission`
--

DROP TABLE IF EXISTS `sys_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_permission` (
  `permission_id` bigint NOT NULL AUTO_INCREMENT COMMENT '权限唯一标识 ID',
  `role_id` tinyint NOT NULL COMMENT '关联角色表(sys_role)的role_id',
  `module_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '功能模块名称(如“病例管理”“算法调用”“系统配置”)',
  `permission_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '权限类型：“查看”“操作”“导出”“配置”',
  `is_enable` tinyint NOT NULL DEFAULT '1' COMMENT '权限是否启用:1-启用, 0-禁用',
  PRIMARY KEY (`permission_id`),
  KEY `fk_permission_role` (`role_id`),
  CONSTRAINT `fk_permission_role` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`role_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_role`
--

DROP TABLE IF EXISTS `sys_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_role` (
  `role_id` tinyint NOT NULL AUTO_INCREMENT COMMENT '角色唯一标识 ID',
  `role_name` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色名称：“临床医师”“系统管理员”',
  `description` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '角色功能描述',
  `create_time` datetime NOT NULL COMMENT '角色创建时间',
  PRIMARY KEY (`role_id`),
  UNIQUE KEY `uk_role_name` (`role_name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_user`
--

DROP TABLE IF EXISTS `sys_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user` (
  `user_id` bigint NOT NULL AUTO_INCREMENT COMMENT '用户唯一标识 ID',
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '登录账号(如医师工号、管理员账号), 唯一不可重复',
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '加密后的登录密码(采用BCrypt算法加密)',
  `real_name` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户真实姓名(医师/管理员姓名)',
  `department` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属科室(如“足踝外科”“信息科”)',
  `title` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '职称(如“主治医师”“主任医师”“工程师”)',
  `role_id` tinyint NOT NULL COMMENT '角色ID:1-临床医师, 2-系统管理员',
  `status` tinyint NOT NULL DEFAULT '1' COMMENT '账号状态:1-启用, 0-禁用',
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '联系电话(脱敏存储)',
  `create_time` datetime NOT NULL COMMENT '账号创建时间',
  `update_time` datetime NOT NULL COMMENT '账号信息最后修改时间',
  `last_login_time` datetime DEFAULT NULL COMMENT '最近一次登录时间',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uk_username` (`username`),
  KEY `fk_user_role` (`role_id`),
  CONSTRAINT `fk_user_role` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`role_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'ankle_surgery_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-28 21:30:20
