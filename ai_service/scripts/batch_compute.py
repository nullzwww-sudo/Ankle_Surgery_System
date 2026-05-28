# -*- coding: utf-8 -*-
import json
import cv2
import numpy as np
import os
import math
from glob import glob

def run_compute(img_dir, contour_json_dir, kp_json_dir, out_dir):
    # =====================
    # 1. 文件夹路径配置
    # =====================
    IMG_DIR = img_dir
    CONTOUR_JSON_DIR = contour_json_dir
    KP_JSON_DIR = kp_json_dir

    # 输出可视化结果和数据汇总的文件夹
    OUT_DIR = out_dir
    os.makedirs(OUT_DIR, exist_ok=True)

    px_per_cm = 100.0  # 物理比例尺

    # =====================
    # 2. 工具函数 (保持不变)
    # =====================
    def draw_point(img, p, name, color):
        p = (int(p[0]), int(p[1]))
        cv2.circle(img, p, 5, color, -1)
        if name:
            cv2.putText(img, name, (p[0]+6, p[1]-6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    def draw_line(img, P, Q, color, name=None):
        P, Q = (int(P[0]),int(P[1])), (int(Q[0]),int(Q[1]))
        cv2.line(img, P, Q, color, 2)
        if name:
            cv2.putText(img, name, ((P[0]+Q[0])//2, (P[1]+Q[1])//2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    def intersect_line_segment(P1, P2, A, B, eps=1e-6):
        x1,y1 = P1; x2,y2 = P2
        x3,y3 = A;  x4,y4 = B
        denom = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
        if abs(denom) < eps: return None
        px = ((x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4)) / denom
        py = ((x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4)) / denom
        if min(x3,x4)-eps <= px <= max(x3,x4)+eps and min(y3,y4)-eps <= py <= max(y3,y4)+eps:
            return (px, py)
        return None

    def line_hits(P1, P2, contours):
        hits = []
        for c in contours:
            for i in range(len(c)):
                p = intersect_line_segment(P1, P2, c[i], c[(i+1)%len(c)])
                if p is not None: hits.append(p)
        return hits

    def horizontal_hits(y, contours):
        hits = []
        for c in contours:
            for i in range(len(c)):
                x1,y1 = c[i]; x2,y2 = c[(i+1)%len(c)]
                if (y1-y)*(y2-y) <= 0 and y1 != y2:
                    t = (y-y1)/(y2-y1)
                    if 0 <= t <= 1: hits.append((x1+t*(x2-x1), y))
        return hits

    def line_dir(P,Q): return (Q[0]-P[0], Q[1]-P[1])

    def angle_between(v1,v2):
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        n1, n2 = math.hypot(*v1), math.hypot(*v2)
        return math.degrees(math.acos(np.clip(dot/(n1*n2), -1, 1)))

    def intersect_lines(P1,v1,P2,v2,eps=1e-6):
        denom = v1[0]*v2[1] - v1[1]*v2[0]
        if abs(denom) < eps: return None
        t = ((P2[0]-P1[0])*v2[1] - (P2[1]-P1[1])*v2[0]) / denom
        return (P1[0]+t*v1[0], P1[1]+t*v1[1])

    def draw_arc(img, center, v1, v2, r, color):
        a1, a2 = math.degrees(math.atan2(v1[1], v1[0])), math.degrees(math.atan2(v2[1], v2[0]))
        if a1 < 0: a1 += 360
        if a2 < 0: a2 += 360
        start_a, end_a = min(a1, a2), max(a1, a2)
        if end_a - start_a > 180: start_a, end_a = end_a, start_a + 360
        cv2.ellipse(img, (int(center[0]), int(center[1])), (r, r), 0, start_a, end_a, color, 2)

    def put_text_degree(img, text, org, color):
        font, scale, thick = cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        if "°" in text:
            base = text.replace("°", "")
            cv2.putText(img, base, org, font, scale, color, thick)
            (tw, th), _ = cv2.getTextSize(base, font, scale, thick)
            cv2.circle(img, (org[0] + tw + 3, org[1] - th + 4), 3, color, 1)
        else:
            cv2.putText(img, text, org, font, scale, color, thick)


    # =====================
    # 3. 单张图像处理主逻辑
    # =====================
    def process_single_measurement(img_path, contour_json, kp_json, out_dir):
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        
        img = cv2.imread(img_path)
        vis = img.copy()

        with open(contour_json) as f: contours = json.load(f)
        with open(kp_json) as f: kp_data = json.load(f)
        
        # 兼容性：如果关键点在列表里嵌套，提取出来
        kps = kp_data.get("keypoints", [])
        if len(kps) < 6:
            raise ValueError("关键点数量不足 6 个")

        tibia  = [np.array(c) for c in contours.get("1", [])]
        fibula = [np.array(c) for c in contours.get("2", [])]
        talus  = [np.array(c) for c in contours.get("3", [])]

        if not tibia or not fibula or not talus:
            raise ValueError("缺少必要的骨骼轮廓数据")

        # 1️⃣ P1 P2 → A B
        P1, P2 = (kps[0]["x"], kps[0]["y"]), (kps[1]["x"], kps[1]["y"])
        A_hits, B_hits = line_hits(P1,P2,fibula), line_hits(P1,P2,tibia)
        A = min(A_hits, key=lambda p:p[0]) if A_hits else P1
        B = max(B_hits, key=lambda p:p[0]) if B_hits else P2

        # 2️⃣ Mab / C D / E F (智能自适应截取)
        Mab = ((A[0]+B[0])/2, (A[1]+B[1])/2)
        
        # 探测当前图片中，胫骨最顶端的 Y 坐标
        tibia_y_min = min([np.min(c[:, 1]) for c in tibia])
        available_len = Mab[1] - tibia_y_min  # 算出从脚踝到顶端总共有多少像素可用

        # 动态确定两个截面的高度
        if available_len >= 13 * px_per_cm:
            # 长度充足，按标准的 8cm 和 13cm 截取
            y_lower = Mab[1] - 8 * px_per_cm
            y_upper = Mab[1] - 13 * px_per_cm
        elif available_len >= 8 * px_per_cm:
            # 长度勉强够 8cm，那么改用 4cm 和 7.5cm 处截取
            y_lower = Mab[1] - 4 * px_per_cm
            y_upper = Mab[1] - 7.5 * px_per_cm
        else:
            # 图片截得太短，直接按可用长度的 40% 和 80% 处截取
            y_lower = Mab[1] - available_len * 0.4
            y_upper = Mab[1] - available_len * 0.8

        h_hits_lower = horizontal_hits(y_lower, tibia)
        h_hits_upper = horizontal_hits(y_upper, tibia)

        if not h_hits_lower or not h_hits_upper:
            raise ValueError(f"无法获取水平截面 (可用像素长度: {available_len:.0f})")
            
        C, D = sorted(h_hits_lower, key=lambda p:p[0])[0], sorted(h_hits_lower, key=lambda p:p[0])[-1]
        E, F = sorted(h_hits_upper, key=lambda p:p[0])[0], sorted(h_hits_upper, key=lambda p:p[0])[-1]
        Mcd, Mef = ((C[0]+D[0])/2, C[1]), ((E[0]+F[0])/2, E[1])

        # 3️⃣ 3–4 → G H → Mgh
        P3, P4 = (kps[2]["x"], kps[2]["y"]), (kps[3]["x"], kps[3]["y"])
        vx,vy = P4[0]-P3[0], P4[1]-P3[1]
        nx,ny = -vy,vx
        n = math.hypot(nx,ny)
        nx/=n; ny/=n

        shift = 0.5*px_per_cm
        gh_hits = line_hits((P3[0]+nx*shift, P3[1]+ny*shift), (P4[0]+nx*shift, P4[1]+ny*shift), talus)
        G = min(gh_hits,key=lambda p:p[0]) if gh_hits else P3
        H = max(gh_hits,key=lambda p:p[0]) if gh_hits else P4
        Mgh = ((G[0]+H[0])/2,(G[1]+H[1])/2)

        # 4️⃣ TAS / TTS 
        v_down = (Mcd[0] - Mef[0], Mcd[1] - Mef[1])
        v_left_AB = (A[0] - B[0], A[1] - B[1])
        v_left_34 = (P3[0] - P4[0], P3[1] - P4[1])

        TAS = angle_between(v_down, v_left_AB)
        TTS = angle_between(v_down, v_left_34)

        # 5️⃣ I / J / TTD_AP
        P5, P6 = (kps[4]["x"], kps[4]["y"]), (kps[5]["x"], kps[5]["y"])
        vGH = line_dir(G,H)
        nGH = (-vGH[1], vGH[0])
        vM  = line_dir(Mcd,Mef)

        I = intersect_lines(Mgh, nGH, P5, line_dir(P5,P6))
        v_perp_M = (-vM[1], vM[0])
        J = intersect_lines(I, v_perp_M, Mcd, vM)
        
        if I is None or J is None:
            raise ValueError("垂线交点计算失败，可能由于线段平行")

        TTD_AP = (math.hypot(I[0]-J[0], I[1]-J[1]) / px_per_cm) * 10

        # 6️⃣ 可视化绘制
        h_img, w_img = vis.shape[:2]
        norm_vM = math.hypot(*vM)
        vM_u = (vM[0]/norm_vM, vM[1]/norm_vM)
        ext_len = max(h_img, w_img)
        draw_line(vis, (Mcd[0]+vM_u[0]*ext_len, Mcd[1]+vM_u[1]*ext_len), 
                    (Mcd[0]-vM_u[0]*ext_len, Mcd[1]-vM_u[1]*ext_len), (0, 255, 0))

        for pts, c in [((C,D), (255,0,0)), ((E,F), (255,0,0)), ((A,B), (255,255,0)), 
                    ((P3,P4), (255,0,255)), ((G,H), (0,255,255)), ((P5,P6), (255,0,0))]:
            draw_line(vis, pts[0], pts[1], c)

        draw_line(vis, Mgh, I, (255, 0, 0))
        draw_line(vis, I, J, (0, 0, 255))

        for name, p in {"A":A, "B":B, "G":G, "H":H, "Mgh":Mgh, "C":C, "D":D, "E":E, "F":F, "Mcd":Mcd, "Mef":Mef}.items():
            draw_point(vis, p, name, (0, 255, 255))
        for name, p in {"1":P1, "2":P2, "3":P3, "4":P4, "5":P5, "6":P6, "I":I, "J":J}.items():
            draw_point(vis, p, name, (0, 0, 255))
        draw_point(vis, Mab, "Mab", (255, 0, 0))

        p_tas, p_tts = Mab, intersect_lines(P3, line_dir(P3, P4), Mcd, v_down)
        if p_tas and p_tts:
            draw_arc(vis, p_tas, v_down, v_left_AB, 55, (255, 255, 255))
            draw_arc(vis, p_tts, v_down, v_left_34, 45, (255, 255, 0))
            tx, ty = int(p_tas[0]) + 10, int(p_tas[1]) + 25
            put_text_degree(vis, f"TAS={TAS:.1f}°", (tx, ty), (255, 255, 255))
            put_text_degree(vis, f"TTS={TTS:.1f}°", (tx, ty+20), (255, 255, 0))

        cv2.putText(vis, "TTD_AP", (int(J[0])+10, int(J[1])+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
        cv2.putText(vis, f"TTD_AP={TTD_AP:.2f} mm", (40, h_img-60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

        # 7️⃣ 保存图像
        out_img_path = os.path.join(out_dir, f"{base_name}_measure_viz.png")
        cv2.imwrite(out_img_path, vis)
        
        # 返回测量结果以便汇总
        return {
        "Image": base_name,
        "TAS_degree": round(TAS, 2),
        "TTS_degree": round(TTS, 2),
        "TTD_AP_mm": round(TTD_AP, 2)
    }

    # =====================
    # 4. 批量执行总入口
    # =====================
    if __name__ == "__main__":
        img_paths = sorted(glob(os.path.join(IMG_DIR, "*.png")))
        
        if not img_paths:
            print(f"❌ 未找到图片，请检查路径: {IMG_DIR}")
            exit()

        print(f"👉 找到 {len(img_paths)} 张图片，开始批量计算测量数据...")
        
        success_count = 0
        all_results = []

        for idx, img_path in enumerate(img_paths, 1):
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            print(f"[{idx}/{len(img_paths)}] 计算中: {base_name} ...", end="", flush=True)

            contour_json = os.path.join(CONTOUR_JSON_DIR, f"{base_name}_contours.json")
            kp_json = os.path.join(KP_JSON_DIR, f"{base_name}_keypoints.json")

            if not os.path.exists(contour_json):
                print(f" ⚠️ 跳过 (缺失轮廓文件: {contour_json})")
                continue
            if not os.path.exists(kp_json):
                print(f" ⚠️ 跳过 (缺失关键点文件: {kp_json})")
                continue

            try:
                measurements = process_single_measurement(img_path, contour_json, kp_json, OUT_DIR)
                all_results.append(measurements)
                print(" 完成 ✔️")
                success_count += 1
            except Exception as e:
                print(f" 失败 ❌ -> {e}")

        # 保存总数据报表
        summary_path = os.path.join(OUT_DIR, "all_measurements_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=4, ensure_ascii=False)

        print("\n" + "="*50)
        print(f"🎉 批量自动测量完成！")
        print(f"✅ 成功处理并画线: {success_count} / {len(img_paths)} 张")
        print(f"📁 测量图纸保存在: {OUT_DIR}")
        print(f"📊 所有病例测量数据统计报表已生成: {summary_path}")
        print("="*50)

    return os.path.join(out_dir, "all_measurements_summary.json")