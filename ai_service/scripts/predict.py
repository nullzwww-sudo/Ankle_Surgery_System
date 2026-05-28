import os
import torch
import pandas as pd
from PIL import Image
from torchvision import transforms, models
from glob import glob

def run_predict(img_dir, out_dir, model_path=r"D:\Ankle_Surgery_System\ai_service\models\aoa\best_model.pth"):
    """
    极简版 AOA 分期预测接口
    :param img_dir: 存放输入图片 (temp_point.jpg) 的临时目录
    :param out_dir: 输出 CSV 文件的目录
    :param model_path: ResNet50 模型权重的路径
    """
    # 1. 自动选择显卡或CPU
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    num_classes = 5 # 假设是 5 个分期

    # 2. 初始化标准的 ResNet50 并修改最后的全连接层适配你的分类数
    # 兼容旧版 torchvision 的写法
    try:
        model = models.resnet50(weights=None)
    except TypeError:
        model = models.resnet50(pretrained=False)
    model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
    
    # 加载你的权重文件
    state_dict = torch.load(model_path, map_location=device)
    # 兼容处理：如果你保存的模型带有 'state_dict' 嵌套字典，就提取出来
    if 'state_dict' in state_dict:
        model.load_state_dict(state_dict['state_dict'])
    else:
        model.load_state_dict(state_dict)
        
    model.to(device)
    model.eval()

    # 3. 图像预处理 (标准的 ImageNet 预处理参数)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.4794,0.4794,0.4794], [0.1806, 0.1806, 0.1806])
    ])

    # 4. 读取图片
    all_paths = glob(os.path.join(img_dir, '*.jpg'))
    if not all_paths: 
        raise FileNotFoundError("未在临时目录找到需要预测的图片")

    img_path = all_paths[0]
    image = Image.open(img_path).convert('RGB')
    input_tensor = transform(image).unsqueeze(0).to(device)

    # 5. 定义你的真实分期名称 (请根据你模型的实际标签顺序修改这里！！！)
    class_names = ['stage 2', 'stage 3a', 'stage 3b1', 'stage 3b2', 'stage 4'] 
    
    # 6. 执行推理
    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
        confidence, predicted_idx = torch.max(probabilities, 0)
        
    stage = class_names[predicted_idx.item()]
    conf_val = round(confidence.item(), 4)

    # 7. 保存为 CSV (为了完美适配 main.py 中 pandas 读取结果的逻辑)
    csv_path = os.path.join(out_dir, 'predictions.csv')
    df = pd.DataFrame({
        'predicted_label': [stage],
        'confidence': [conf_val]
    })
    df.to_csv(csv_path, index=False)
    
    return csv_path