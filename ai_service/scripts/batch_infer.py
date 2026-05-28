# -*- coding: utf-8 -*-
import os
import json
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from PIL import Image, ImageDraw
from torchvision import transforms
from scipy.ndimage import gaussian_filter
import argparse
from glob import glob

try:
    from mmpose.models import build_backbone, build_neck, build_head
    print("MMPose 组件导入成功。")
except ImportError as e:
    raise ImportError("请确保已安装 MMPose") from e

# ==========================================
# 1. 核心组件：跳跃连接空间门控 (Skip-CA)
# ==========================================
class CoordAtt(nn.Module):
    def __init__(self, inp, oup, reduction=32):
        super(CoordAtt, self).__init__()
        self.pool_h = nn.AdaptiveAvgPool2d((None, 1))
        self.pool_w = nn.AdaptiveAvgPool2d((1, None))
        mip = max(8, inp // reduction)
        self.conv1 = nn.Conv2d(inp, mip, kernel_size=1, stride=1, padding=0)
        self.bn1 = nn.BatchNorm2d(mip)
        self.act = nn.GELU()
        self.conv_h = nn.Conv2d(mip, oup, kernel_size=1, stride=1, padding=0)
        self.conv_w = nn.Conv2d(mip, oup, kernel_size=1, stride=1, padding=0)

    def forward(self, x):
        identity = x
        n, c, h, w = x.size()
        x_h = self.pool_h(x)
        x_w = self.pool_w(x).permute(0, 1, 3, 2)
        y = torch.cat([x_h, x_w], dim=2)
        y = self.act(self.bn1(self.conv1(y)))
        x_h, x_w = torch.split(y, [h, w], dim=2)
        x_w = x_w.permute(0, 1, 3, 2)
        a_h = self.conv_h(x_h).sigmoid()
        a_w = self.conv_w(x_w).sigmoid()
        return identity * a_w * a_h

# ==========================================
# 2. 模型架构：MMPoseHTCModel_SE (对应 Exp4)
# ==========================================
class MMPoseHTCModel_SE(nn.Module):
    def __init__(self, num_joints=6, input_size=512):
        super().__init__()
        self.input_size = input_size

        backbone_cfg = dict(
            type='HTC', num_stages=4, num_layers=[1, 1, 1, 1],
            patch_sizes=[3, 3, 3, 3], strides=[2, 2, 2, 2],
            paddings=[1, 1, 1, 1], num_heads=[1, 2, 5, 8],
            chratio=[8, 4, 2, 1], out_indices=(0, 1, 2, 3)
        )
        self.backbone = build_backbone(backbone_cfg)

        self.skip_ca = nn.ModuleList([
            CoordAtt(64, 64, reduction=8),    
            CoordAtt(128, 128, reduction=16), 
            CoordAtt(320, 320, reduction=32), 
            CoordAtt(512, 512, reduction=32)  
        ])

        neck_cfg = dict(
            type='Deconv_FPN_Neck',
            in_channels=[64, 128, 320, 512],
            out_channels=256, num_deconv_layers=2,
            num_deconv_filters=(320, 128), num_deconv_kernels=(4, 4),
        )
        self.neck = build_neck(neck_cfg)

        head_cfg = dict(
            type='TopdownSimple_Heatmap_ConvHead',
            in_channels=256, feat_channels=256,
            out_channels=num_joints,
            loss_keypoint=dict(type='JointsMSELoss', use_target_weight=False)
        )
        self.head = build_head(head_cfg)

    def forward(self, x):
        if x.shape[2:] != (self.input_size, self.input_size):
            x = F.interpolate(x, size=(self.input_size, self.input_size), mode='bilinear', align_corners=False)

        feats = self.backbone(x) 
        refined_feats = []
        for i, feat in enumerate(feats):
            refined_feats.append(self.skip_ca[i](feat))

        fused = self.neck(refined_feats) 
        heatmaps = self.head(fused)
        heatmaps = F.interpolate(heatmaps, size=(128, 128), mode='bilinear', align_corners=False)
        return heatmaps

# ==========================================
# 3. 亚像素特征提取
# ==========================================
def extract_keypoints_subpixel(heatmaps):
    num_joints = heatmaps.shape[0]
    keypoints = np.zeros((num_joints, 2))
    for i in range(num_joints):
        smoothed = gaussian_filter(heatmaps[i], sigma=1)
        y, x = np.unravel_index(np.argmax(smoothed), smoothed.shape)
        
        px, py = 0.0, 0.0
        if 1 < x < smoothed.shape[1] - 1 and 1 < y < smoothed.shape[0] - 1:
            diff_x = smoothed[y, x+1] - smoothed[y, x-1]
            diff_y = smoothed[y+1, x] - smoothed[y-1, x]
            px = np.sign(diff_x) * 0.25
            py = np.sign(diff_y) * 0.25
            
        keypoints[i] = [x + px, y + py]
    return keypoints

# ==========================================
# 4. 单张图片处理函数 (集成推理逻辑)
# ==========================================
def process_single_image_ensemble(image_path, models, output_dir, device='cuda'):
    num_joints = 6
    
    # 1. 读取与预处理
    image_orig = Image.open(image_path).convert('RGB')
    w, h = image_orig.size

    transform = transforms.Compose([
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    image_tensor = transform(image_orig).unsqueeze(0).to(device)

    # 2. ★ 多模型集成推理 (Ensemble) ★
    all_heatmaps = []
    with torch.no_grad():
        for model in models:
            # 拿到单模型的热图，shape: (6, 128, 128)
            heatmaps = model(image_tensor)[0].cpu().numpy()  
            all_heatmaps.append(heatmaps)
    
    # 将 5 个模型的热图在第 0 维度进行堆叠然后求平均
    # all_heatmaps shape: (5, 6, 128, 128) -> avg_heatmaps shape: (6, 128, 128)
    avg_heatmaps = np.mean(all_heatmaps, axis=0)

    # 3. 从平均后的热图中提取亚像素坐标
    keypoints_128 = extract_keypoints_subpixel(avg_heatmaps)
    keypoints_512 = keypoints_128 * 4.0

    # 4. 映射回物理尺寸
    scale_x = w / 512.0
    scale_y = h / 512.0

    keypoints_orig = []
    for x, y in keypoints_512:
        keypoints_orig.append({
            "x": round(float(x * scale_x), 2),
            "y": round(float(y * scale_y), 2)
        })

    # 5. 可视化与保存
    vis_img = image_orig.copy()
    draw = ImageDraw.Draw(vis_img)
    for kp in keypoints_orig:
        x, y = kp["x"], kp["y"]
        draw.ellipse((x-4, y-4, x+4, y+4), fill='red', outline='yellow')

    base = os.path.splitext(os.path.basename(image_path))[0]
    vis_dir = os.path.join(output_dir, "vis")
    json_dir = os.path.join(output_dir, "json")
    os.makedirs(vis_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    vis_img.save(os.path.join(vis_dir, f"{base}_vis.png"))
    with open(os.path.join(json_dir, f"{base}_keypoints.json"), 'w', encoding='utf-8') as f:
        json.dump({
            "image": os.path.basename(image_path),
            "num_keypoints": num_joints,
            "keypoints": keypoints_orig
        }, f, indent=2)

# ==========================================
# 5. 批量处理主程序
# ==========================================
def run_batch_infer(img_dir, out_dir, model_path=r"D:\Ankle_Surgery_System\ai_service\models\keypoint"):
    parser = argparse.ArgumentParser("HTC 5折交叉验证集成批量推理")
    parser.add_argument('--input_dir', type=str, default = img_dir, help='需要推理的图片文件夹路径')
    parser.add_argument('--weights_dir', type=str, default = model_path, help='存放 5 个折叠模型的文件夹路径 (例如 exp4/)')
    parser.add_argument('--out_dir', type=str, default = out_dir, help='结果保存目录')
    args = parser.parse_args()

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # ==========================
    # 加载多个模型
    # ==========================
    weight_paths = glob(os.path.join(args.weights_dir, "*.pth"))
    if not weight_paths:
        print(f"❌ 在 {args.weights_dir} 中没有找到任何 .pth 模型文件。")
        exit()

    print(f"🚀 准备加载 {len(weight_paths)} 个模型进行 Ensemble 推理...")
    models = []
    for w_path in weight_paths:
        try:
            model = MMPoseHTCModel_SE(num_joints=6, input_size=512)
            model.load_state_dict(torch.load(w_path, map_location=device))
            model.to(device)
            model.eval()
            models.append(model)
            print(f"  ✅ 成功加载: {os.path.basename(w_path)}")
        except Exception as e:
            print(f"  ❌ 无法加载 {w_path}，报错: {e}")
            exit()

    # ==========================
    # 查找所有图片并循环
    # ==========================
    img_paths = sorted(glob(os.path.join(args.input_dir, "*.jpg")))
    img_paths.extend(sorted(glob(os.path.join(args.input_dir, "*.png")))) # 支持png

    if not img_paths:
        print(f"❌ 在 {args.input_dir} 中没有找到任何 jpg/png 图片。")
        exit()

    print(f"\n👉 共找到 {len(img_paths)} 张图片，开始批量推理...")
    success_count = 0
    start_time = time.time()

    for idx, img_path in enumerate(img_paths, 1):
        file_name = os.path.basename(img_path)
        print(f"[{idx}/{len(img_paths)}] 处理中: {file_name} ...", end="", flush=True)
        
        try:
            # 传递包含 5 个模型的列表
            process_single_image_ensemble(img_path, models, args.out_dir, device)
            print(" 完成 ✔️")
            success_count += 1
        except Exception as e:
            print(f" 失败 ❌\n   -> 错误信息: {e}")

    total_time = time.time() - start_time
    print("\n" + "="*50)
    print(f"🎉 Ensemble 批量推理任务圆满结束！")
    print(f"✅ 成功处理: {success_count}/{len(img_paths)} 张")
    print(f"⏱️ 总耗时: {total_time:.2f} 秒 (平均每张 {(total_time/len(img_paths)):.2f} 秒)")
    print(f"📁 结果已分类存放至: {args.out_dir} 下的 vis 和 json 文件夹中")
    print("="*50)

    return True