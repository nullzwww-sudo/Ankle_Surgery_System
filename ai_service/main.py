import os
import uuid
import shutil
import base64
import json
import pandas as pd
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

# 导入你改造后的算法函数
from scripts.predict import run_predict
from scripts.batch_infer import run_batch_infer
from scripts.batch_infer_seg import run_seg_infer
from scripts.batch_mark2seg import run_mark2seg
from scripts.batch_compute import run_compute
from scripts.batch_view import run_view

# ==========================================
# Gemini 大模型配置 (带本地代理穿透)
# ==========================================
# ⚠️ 注意：Python 脚本默认不走系统代理。
# 请将 7890 替换为你 VPN 的真实端口 (Clash 通常是 7890，v2rayN 通常是 10809)
os.environ["http_proxy"] = "http://127.0.0.1:7897"
os.environ["https_proxy"] = "http://127.0.0.1:7897"

# 填入你刚刚申请的 Gemini API Key
genai.configure(api_key="AIzaSyDfCVWAWBL2hSlr_2hig_TAVSNIU5g7Vpw")

# 初始化 Gemini 模型 (推荐使用 1.5 Pro，逻辑推理最强)
gemini_model = genai.GenerativeModel('gemini-1.5-pro')

app = FastAPI(title="Ankle Surgery AI Service", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

BASE_TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_workspace")

def create_temp_workspace():
    task_id = str(uuid.uuid4().hex)
    task_dir = os.path.join(BASE_TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)
    return task_dir, task_id

@app.post("/api/ai/aoa_stage")
async def get_aoa_stage(point_image: UploadFile = File(...)):
    """接口 A：获取 AOA 分期"""
    task_dir, _ = create_temp_workspace()
    try:
        img_path = os.path.join(task_dir, "temp_point.jpg")
        with open(img_path, "wb") as f: f.write(await point_image.read())
        
        # 1. 运行预测算法
        csv_path = run_predict(img_dir=task_dir, out_dir=task_dir)
        
        # 2. 从真实的 CSV 文件读取结果
        df = pd.read_csv(csv_path)
        stage = df.iloc[0]['predicted_label']
        confidence = float(df.iloc[0]['confidence'])
        
        return {"code": 200, "message": "success", "data": {"stage": stage, "confidence": confidence}}
    except Exception as e:
        import traceback          # 新增：导入追溯模块
        traceback.print_exc()     # 新增：强制在终端打印详细红字报错！
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(task_dir, ignore_errors=True)

@app.post("/api/ai/calculate_plan")
async def calculate_angles(
    point_image: UploadFile = File(...), seg_image: UploadFile = File(...),
    point_json_content: str = Form(...), seg_json_content: str = Form(...)
):
    """接口 B：关键点映射与角度计算"""
    task_dir, _ = create_temp_workspace()
    
    dir_point_img = os.path.join(task_dir, "point-roi", "img")
    dir_point_json = os.path.join(task_dir, "point-roi", "json")
    dir_seg_img = os.path.join(task_dir, "seg-roi", "png")
    dir_seg_json = os.path.join(task_dir, "seg-roi", "json")
    for d in [dir_point_img, dir_point_json, dir_seg_img, dir_seg_json]: os.makedirs(d, exist_ok=True)

    try:
        base_name = "case_001"
        with open(os.path.join(dir_point_img, f"{base_name}_point.jpg"), "wb") as f: f.write(await point_image.read())
        with open(os.path.join(dir_seg_img, f"{base_name}_seg.png"), "wb") as f: f.write(await seg_image.read())
        with open(os.path.join(dir_point_json, f"{base_name}_point.json"), "w") as f: f.write(point_json_content)
        with open(os.path.join(dir_seg_json, f"{base_name}_seg.json"), "w") as f: f.write(seg_json_content)

        # 调度算法 B
        run_batch_infer(img_dir=dir_point_img, out_dir=dir_point_json)
        run_seg_infer(input_dir=dir_seg_img, out_dir=dir_seg_json)
        run_mark2seg(dir_point_json=dir_point_json, dir_seg_json=dir_seg_json, dir_kp_json=dir_point_json, out_dir=dir_seg_json)
        summary_path = run_compute(img_dir=dir_seg_img, contour_json_dir=dir_seg_json, kp_json_dir=dir_seg_json, out_dir=task_dir)
        run_view(img_dir=dir_seg_img, json_dir=dir_seg_json, out_dir=task_dir)

        # 获取真实结果 (读取你提供的 all_measurements_summary.json)
        with open(summary_path, "r", encoding="utf-8") as f:
            data_list = json.load(f)
            real_data = data_list[0]  # 取第一条数据
            
        vis_img_path = os.path.join(task_dir, f"{base_name}_vis.png")
        with open(vis_img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        return {
            "code": 200, "message": "success",
            "data": {
                "tas": real_data["TAS_degree"],
                "tts": real_data["TTS_degree"],
                "ttd_ap_mm": real_data["TTD_AP_mm"],
                "vis_image_base64": f"data:image/png;base64,{encoded_string}"
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/generate_plan")
async def generate_surgical_plan(stage: str = Form(...), tas: float = Form(...), tts: float = Form(...), ttd: float = Form(...), age: int = Form(...), gender: str = Form(...)):
    """接口 C：调用 Gemini 生成手术规划"""
    prompt = f"""
    你是一名资深的足踝外科专家。现在有一名患者，基本信息如下：
    年龄：{age}岁，性别：{gender}。
    AI 测量的影像学参数如下：
    - AOA 分期：{stage}
    - TAS 角：{tas}°
    - TTS 角：{tts}°
    - TTD 距离：{ttd} mm
    
    请根据以上参数，严格按照以下 JSON 格式输出手术规划方案，不要输出任何其他废话：
    {{"osteotomy_position": "截骨位置", "osteotomy_angle": "截骨角度数值", "distraction_height": "撑开高度数值", "fixation_method": "固定方式建议"}}
    """
    try:
        # 调用 Gemini 并强制要求它以 JSON 格式返回结果
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        plan_json = json.loads(response.text)
        return {"code": 200, "message": "success", "data": plan_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)