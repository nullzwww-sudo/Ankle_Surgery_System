package com.ankle.backend.mapper;

import com.ankle.backend.entity.ImageAnnotation;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ImageAnnotationMapper {
    int insert(ImageAnnotation imageAnnotation);
}