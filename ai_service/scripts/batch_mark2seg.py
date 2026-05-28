# -*- coding: utf-8 -*-
import os
import json
from glob import glob

def run_mark2seg(dir_point_json, dir_seg_json, dir_kp_json, out_dir):
    # ==========================================
    # 1. 文件夹路径配置
    # ==========================================
    # 你的三个输入文件夹
    DIR_POINT_JSON = dir_point_json
    DIR_SEG_JSON = dir_seg_json
    DIR_KP_JSON = dir_kp_json

    # 转换后输出的 JSON 文件夹 (建议放在 seg-roi 下面，因为坐标已经对齐到 seg 图像了)
    OUT_DIR = out_dir
    os.makedirs(OUT_DIR, exist_ok=True)

    A_SIZE = 512  # point-roi 裁剪图的固定大小

    # ==========================================
    # 2. 查找并批量处理
    # ==========================================
    # 我们以 point-roi/json 文件夹作为基准来遍历
    point_json_paths = glob(os.path.join(DIR_POINT_JSON, "*_point.json"))

    if not point_json_paths:
        print(f"❌ 在 {DIR_POINT_JSON} 中没有找到任何 *_point.json 文件。")
        exit()

    print(f"👉 找到 {len(point_json_paths)} 个基础裁剪配置，开始批量坐标映射...")

    success_count = 0

    for point_path in point_json_paths:
        # 提取核心文件名，例如从 "zhuqingda_point.json" 提取出 "zhuqingda"
        filename = os.path.basename(point_path)
        base_name = filename.replace("_point.json", "")
        
        # 拼凑出对应的 B 文件 (seg JSON) 和关键点文件的路径
        seg_path = os.path.join(DIR_SEG_JSON, f"{base_name}_seg.json")
        
        # 注意：根据你之前的脚本，关键点结果可能叫 _point_keypoints_combo.json 或 _point_keypoints.json
        # 这里做了一个兼容处理，优先找 combo，找不到就找普通的
        kp_path = os.path.join(DIR_KP_JSON, f"{base_name}_point_keypoints_combo.json")
        if not os.path.exists(kp_path):
            kp_path = os.path.join(DIR_KP_JSON, f"{base_name}_point.json")

        # 检查三个文件是否都齐备
        if not os.path.exists(seg_path):
            print(f"⚠️ 跳过 {base_name}: 找不到对应的 Seg JSON -> {seg_path}")
            continue
        if not os.path.exists(kp_path):
            print(f"⚠️ 跳过 {base_name}: 找不到对应的 关键点 JSON -> {kp_path}")
            continue

        # ==========================================
        # 3. 执行坐标映射逻辑
        # ==========================================
        try:
            with open(point_path, "r", encoding="utf-8") as f:
                A = json.load(f)["crop_info"]

            with open(seg_path, "r", encoding="utf-8") as f:
                B = json.load(f)["crop_info"]

            with open(kp_path, "r", encoding="utf-8") as f:
                kp_data = json.load(f)

            # 关键：从 512 → A 实际裁剪尺寸 的缩放比例
            scale_x = A["sw"] / float(A_SIZE)
            scale_y = A["sh"] / float(A_SIZE)

            # 动态使用 base_name 构造 target image name
            out = {
                "image": f"{base_name}_seg.png", 
                "num_keypoints": kp_data.get("num_keypoints", len(kp_data.get("keypoints", []))),
                "keypoints": []
            }

            for pt in kp_data.get("keypoints", []):
                xA_512 = pt["x"]
                yA_512 = pt["y"]

                # Step 1：还原到 A 的真实裁剪尺寸
                xA = xA_512 * scale_x
                yA = yA_512 * scale_y

                # Step 2：A → 原图 → B
                xB = xA + A["sx"] - B["sx"]
                yB = yA + A["sy"] - B["sy"]

                # 判断是否在 B 的视野范围内
                visible = int(
                    0 <= xB < B["sw"] and
                    0 <= yB < B["sh"]
                )

                out["keypoints"].append({
                    "x": round(float(xB), 2),
                    "y": round(float(yB), 2),
                    "visible": visible
                })

            # ==========================================
            # 4. 保存映射后的 JSON
            # ==========================================
            out_json_path = os.path.join(OUT_DIR, f"{base_name}_points.json")
            with open(out_json_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2)
                
            print(f"✔️ 成功映射: {base_name}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 处理 {base_name} 时发生错误: {e}")

    print("\n" + "="*50)
    print(f"🎉 批量坐标映射完成！")
    print(f"✅ 成功处理: {success_count} / {len(point_json_paths)} 组数据")
    print(f"📁 最终坐标结果保存在: {OUT_DIR}")
    print("="*50)

    return True