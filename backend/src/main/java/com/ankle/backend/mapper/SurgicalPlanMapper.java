package com.ankle.backend.mapper;

import com.ankle.backend.entity.SurgicalPlan;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface SurgicalPlanMapper {
    int insert(SurgicalPlan surgicalPlan);
}