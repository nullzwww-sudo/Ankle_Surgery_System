package com.ankle.backend.mapper;

import com.ankle.backend.entity.AoaStageResult;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface AoaStageResultMapper {
    int insert(AoaStageResult aoaStageResult);

    // 【新增加的方法】根据病例ID查询最新的分期结果，用来获取 stageId 和 patientId
    @Select("SELECT * FROM aoa_stage_result WHERE case_id = #{caseId} ORDER BY stage_id DESC LIMIT 1")
    AoaStageResult selectLatestByCaseId(Long caseId);
}