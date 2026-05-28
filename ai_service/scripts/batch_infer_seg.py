# -*- coding: utf-8 -*-
# seg-batch-infer-ensemble.py
# 终极 5折集成版：5模型概率求均值 + 尺寸自适应 + 安全TTA + 去噪后处理 + 批量处理循环 + 输出分类文件夹

import os
import time
import json
import cv2
import torch
import torch.nn as nn
import numpy as np
from glob import glob
import segmentation_models_pytorch as smp

# ==========================================
# 1. 核心模型定义
# ==========================================
class BoundaryAwareUNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = smp.Unet(
            encoder_name="tu-convnext_tiny",
            encoder_weights=None, # 推理时不需要预训练权重
            in_channels=1,
            classes=5, # 4类分割 + 1类边缘
        )
        
    def forward(self, x):
        logits = self.model(x)
        seg_logits = logits[:, :4, :, :]
        edge_logits = logits[:, 4, :, :]
        return seg_logits, edge_logits

# ==========================================
# 2. 核心算法组件
# ==========================================
def keep_largest_connected_component(mask, num_classes=4):
    """后处理：保留每个类别的最大连通域，消除飞地噪声"""
    cleaned_mask = np.zeros_like(mask)
    for class_id in range(1, num_classes):
        binary_mask = (mask == class_id).astype(np.uint8)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
        if num_labels > 1:
            largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            cleaned_mask[labels == largest_label] = class_id
    return cleaned_mask

def preprocess(img_path, clahe, device):
    """预处理：旋转检查、CLAHE、32倍数动态Padding"""
    gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise FileNotFoundError(f"无法读取图片: {img_path}")
        
    rotated = gray.shape[0] < gray.shape[1]
    orig = cv2.imread(img_path)
    
    if rotated:
        gray = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
        orig = cv2.rotate(orig, cv2.ROTATE_90_CLOCKWISE)
        
    curr_h, curr_w = gray.shape
    gray = clahe.apply(gray).astype(np.float32) / 255.0
    
    pad_h = (curr_h + 31) // 32 * 32
    pad_w = (curr_w + 31) // 32 * 32
    
    padded = np.zeros((pad_h, pad_w), dtype=np.float32)
    padded[:curr_h, :curr_w] = gray 
    
    x = torch.from_numpy(padded[np.newaxis, np.newaxis, ...]).to(device)
    return x, orig, rotated, (curr_h, curr_w)

def tta_predict(model, x):
    """安全版测试时增强：仅进行水平左右翻转"""
    preds = []
    seg_logits, _ = model(x)
    preds.append(torch.softmax(seg_logits, dim=1))
    
    aug_flip = torch.flip(x, dims=[3]) 
    seg_logits_flip, _ = model(aug_flip)
    pred_flip = torch.softmax(seg_logits_flip, dim=1)
    preds.append(torch.flip(pred_flip, dims=[3]))
        
    return torch.stack(preds).mean(0)

# ==========================================
# 3. 单张图片处理主干 (集成逻辑修改点)
# ==========================================
def process_single_image(img_path, models, clahe, device, use_tta, out_dirs):
    name = os.path.splitext(os.path.basename(img_path))[0]

    # 1. 预处理
    x, orig_rotated, rotated, (orig_h, orig_w) = preprocess(img_path, clahe, device) 

    # 2. ★ 多模型集成推理 (Ensemble) ★
    all_preds = []
    with torch.no_grad():
        for model in models:
            if use_tta:
                pred = tta_predict(model, x) # TTA输出已经是概率了
            else:
                seg_logits, _ = model(x)
                pred = torch.softmax(seg_logits, dim=1)
            all_preds.append(pred)
    
    # 3. 将 5 个模型的概率图在第 0 维度堆叠并求平均
    avg_pred = torch.stack(all_preds).mean(dim=0)

    # 4. 尺寸还原与后处理去噪
    avg_pred = avg_pred[:, :, :orig_h, :orig_w]
    raw_mask = avg_pred[0].argmax(0).cpu().numpy().astype(np.uint8)
    mask = keep_largest_connected_component(raw_mask)

    # 5. 颜色渲染
    color = np.zeros_like(orig_rotated)
    color[mask == 1] = [255, 0,   0]   # 胫骨 (Red)
    color[mask == 2] = [0,   255, 0]   # 腓骨 (Green)
    color[mask == 3] = [0,   0, 255]   # 距骨 (Blue)
    overlay_rotated = cv2.addWeighted(orig_rotated, 0.6, color, 0.4, 0)
    
    # 6. 逆旋转 (还原到原始朝向)
    if rotated:
        mask = cv2.rotate(mask, cv2.ROTATE_90_COUNTERCLOCKWISE)
        overlay_rotated = cv2.rotate(overlay_rotated, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # 7. 提取轮廓与保存 JSON
    contours_data = {}
    contour_visual = overlay_rotated.copy()
    
    for class_id in [1, 2, 3]:
        class_mask = (mask == class_id).astype(np.uint8) * 255
        contours, _ = cv2.findContours(class_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contours_data[str(class_id)] = [c.reshape(-1, 2).tolist() for c in contours]
        
        if class_id == 1: c_color = (0, 0, 255)
        elif class_id == 2: c_color = (0, 255, 0)
        elif class_id == 3: c_color = (255, 0, 0)
        
        for contour_coords in contours_data[str(class_id)]:
            contour_np = np.array(contour_coords, dtype=np.int32).reshape((-1, 1, 2))
            cv2.drawContours(contour_visual, [contour_np], -1, c_color, 2) 

    # 8. 按类别写入硬盘对应的子文件夹
    with open(os.path.join(out_dirs['jsons'], f"{name}_contours.json"), "w") as f:
        json.dump(contours_data, f, indent=4)
        
    cv2.imwrite(os.path.join(out_dirs['masks'], f"{name}_pred.png"), mask)
    cv2.imwrite(os.path.join(out_dirs['overlays'], f"{name}_overlay.png"), overlay_rotated)
    cv2.imwrite(os.path.join(out_dirs['contours_viz'], f"{name}_contours_viz.png"), contour_visual)

# ==========================================
# 4. 批量运行总入口
# ==========================================
def run_seg_infer(input_dir, out_dir, weight_dir=r"D:\Ankle_Surgery_System\ai_service\models\segmentation"):    # ---- 请核对以下路径配置 ----
    # 存放 5 个 pth 模型权重的文件夹路径
    MODELS_DIR = weight_dir
    
    # 待处理的 PNG 图片文件夹
    INPUT_DIR = input_dir
    
    # 输出结果的保存根文件夹
    OUTPUT_DIR = out_dir
    
    # 是否开启 TTA (由于用了5个模型，建议填 False 即可，否则推理时间翻倍)
    USE_TTA = False
    # ----------------------------

    # 自动创建分类存放的子文件夹
    out_dirs = {
        'masks': os.path.join(OUTPUT_DIR, "masks"),
        'overlays': os.path.join(OUTPUT_DIR, "overlays"),
        'contours_viz': os.path.join(OUTPUT_DIR, "contours_viz"),
        'jsons': os.path.join(OUTPUT_DIR, "jsons")
    }
    for d in out_dirs.values():
        os.makedirs(d, exist_ok=True)

    device = torch.device("" if torch.cuda.is_available() else "cpu")
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))

    # ==========================================
    # 加载多个模型
    # ==========================================
    weight_paths = glob(os.path.join(MODELS_DIR, "*.pth"))
    if not weight_paths:
        print(f"❌ 在 {MODELS_DIR} 中没有找到任何 .pth 模型文件。")
        exit()

    print(f"🚀 正在加载 {len(weight_paths)} 个模型进行 Ensemble 推理...")
    models = []
    for w_path in weight_paths:
        try:
            model = BoundaryAwareUNet()
            model.load_state_dict(torch.load(w_path, map_location=device))
            model.to(device)
            model.eval()
            models.append(model)
            print(f"  ✅ 成功加载: {os.path.basename(w_path)}")
        except Exception as e:
            print(f"  ❌ 无法加载 {w_path}，报错: {e}")
            exit()

    img_paths = sorted(glob(os.path.join(INPUT_DIR, "*.png")))
    if not img_paths:
        print(f"❌ 在 {INPUT_DIR} 中没有找到任何 PNG 图片。")
        exit()

    print(f"\n👉 共找到 {len(img_paths)} 张测试图片，开始批量 5折集成 推理...")
    success_count = 0
    start_time = time.time()

    for idx, img_path in enumerate(img_paths, 1):
        file_name = os.path.basename(img_path)
        print(f"[{idx}/{len(img_paths)}] 集成处理中: {file_name} ...", end="", flush=True)
        
        try:
            # 将 models 列表传进去
            process_single_image(img_path, models, clahe, device, use_tta=USE_TTA, out_dirs=out_dirs)
            print(" 完成 ✔️")
            success_count += 1
        except Exception as e:
            print(f" 失败 ❌\n   -> 错误信息: {e}")

    total_time = time.time() - start_time
    print("\n" + "="*50)
    print(f"🎉 批量 5折集成 分割任务圆满结束！")
    print(f"✅ 成功处理: {success_count}/{len(img_paths)} 张")
    print(f"⏱️ 总耗时: {total_time:.2f} 秒 (平均每张 {(total_time/len(img_paths)):.2f} 秒)")
    print(f"📁 结果已分类存放至: {OUTPUT_DIR}")
    print("="*50)

    return True