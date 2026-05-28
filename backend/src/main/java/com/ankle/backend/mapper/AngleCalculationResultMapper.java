package com.ankle.backend.mapper;

import com.ankle.backend.entity.AngleCalculationResult;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AngleCalculationResultMapper {
    int insert(AngleCalculationResult angleCalculationResult);
}