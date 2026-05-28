# -*- coding: utf-8 -*-
import os
import json
from glob import glob
from PIL import Image, ImageDraw

def run_view(img_dir, json_dir, out_dir):
    # ==========================================
    # 1. 文件夹路径配置
    # ==========================================
    # 输入文件夹
    IMG_DIR = img_dir
    JSON_DIR = json_dir

    # 输出文件夹（自动创建）
    OUT_DIR = out_dir
    os.makedirs(OUT_DIR, exist_ok=True)

    # ==========================================
    # 2. 查找并批量处理
    # ==========================================
    # 获取所有 png 图片
    img_paths = sorted(glob(os.path.join(IMG_DIR, "*.png")))

    if not img_paths:
        print(f"❌ 在 {IMG_DIR} 中没有找到任何 PNG 图片。")
        exit()

    print(f"👉 找到 {len(img_paths)} 张图片，开始批量关键点可视化...")

    success_count = 0

    for img_path in img_paths:
        # 提取基本文件名，例如 "zhuqingda_seg"
        filename = os.path.basename(img_path)
        base_name = os.path.splitext(filename)[0]
        
        # 拼凑出对应的 JSON 路径
        kp_path = os.path.join(JSON_DIR, f"{base_name}_keypoints.json")
        out_path = os.path.join(OUT_DIR, f"{base_name}_vis.png")

        # 检查对应的 JSON 文件是否存在
        if not os.path.exists(kp_path):
            print(f"⚠️ 跳过 {filename}: 找不到对应的关键点 JSON -> {kp_path}")
            continue

        # ==========================================
        # 3. 执行可视化逻辑
        # ==========================================
        try:
            # 读取图片和关键点数据
            img = Image.open(img_path).convert("RGB")
            draw = ImageDraw.Draw(img)

            with open(kp_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 画点
            R = 6  # 点的半径
            for i, kp in enumerate(data.get("keypoints", [])):
                if kp.get("visible", 1) == 0:
                    continue

                x, y = kp["x"], kp["y"]
                
                # 画红色圆点，带白色边框
                draw.ellipse(
                    (x - R, y - R, x + R, y + R),
                    fill=(255, 0, 0),      # 红色
                    outline=(255, 255, 255) # 白色轮廓线
                )
                # 在点旁边标注编号 (黄色)
                draw.text((x + 5, y + 5), str(i + 1), fill=(255, 255, 0))

            # 保存可视化结果
            img.save(out_path)
            print(f"✔️ 成功可视化: {filename}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 处理 {filename} 时发生错误: {e}")

    print("\n" + "="*50)
    print(f"🎉 批量可视化完成！")
    print(f"✅ 成功处理: {success_count} / {len(img_paths)} 张图片")
    print(f"📁 可视化结果保存在: {OUT_DIR}")
    print("="*50)

    return True