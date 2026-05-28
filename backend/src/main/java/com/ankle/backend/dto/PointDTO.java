package com.ankle.backend.dto;

public class PointDTO {
    
    private Double x;
    private Double y;

    // 手动生成 Getter 和 Setter，绝对不会报错
    public Double getX() {
        return x;
    }

    public void setX(Double x) {
        this.x = x;
    }

    public Double getY() {
        return y;
    }

    public void setY(Double y) {
        this.y = y;
    }
}