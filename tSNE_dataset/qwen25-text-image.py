import json
import numpy as np
from PIL import Image
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from tqdm import tqdm
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
import torch
import os


# ============================
# 2. 单样本多模态 embedding 提取函数 (修改为提取所有层的 Embedding)
# ============================
def get_multimodal_layers_embeddings(text: str, image_path: str, model, processor, layers_to_extract: list):
    """
    对单个多模态样本进行推理，并返回指定层级的 Embedding 字典。
    """
    image = Image.open(image_path).convert("RGB")

    # ChatML 输入格式
    prompt = [
        {"role": "user", "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": text + '<image>'}
        ]}
    ]
    formatted_text = processor.apply_chat_template(
        prompt,
        add_generation_prompt=False,
        tokenize=False,
        padding=False
    )
    inputs = processor(
        text=[formatted_text],
        images=[image],
        return_tensors="pt"
    ).to(model.device)

    # 视觉 + 文本编码
    with torch.no_grad():
        # 关键修改：设置 output_hidden_states=True
        outputs = model(**inputs, output_hidden_states=True)

    hidden_states = outputs.hidden_states

    layer_embeddings = {}
    for layer_idx in layers_to_extract:
        if layer_idx < len(hidden_states):
            # Mean pooling
            layer_output = hidden_states[layer_idx]
            embedding = layer_output.mean(dim=1).cpu().numpy()[0]
            layer_embeddings[layer_idx] = embedding
        else:
            # 记录错误但不中断计算
            print(f"Warning: Layer index {layer_idx} out of range ({len(hidden_states) - 1}). Skipping.")

    return layer_embeddings


# ============================
# 3. 数据处理辅助函数
# ============================
def load_and_prepare_data_multimodal(dataset_names: list, data_base_path="./",
                                     image_base_path="/mnt/sda/zzh/verl/data"):
    """
    加载指定的数据集，合并文本和图像路径，并记录每个数据集的长度。
    """
    if len(dataset_names) > 5:
        raise ValueError("最多支持 5 个数据集进行同时计算。")

    all_texts = []
    all_image_paths = []
    dataset_lengths = {}  # 存储 {name: length}

    for name in dataset_names:
        # 假设 JSON 文件路径为 {data_base_path}/{name}.json
        data_file_path = os.path.join(data_base_path, f'{name.lower()}.json')

        try:
            with open(data_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            current_texts = []
            current_image_paths = []

            # 假设每个数据集的图片子目录为 {image_base_path}/{name.lower()}/image/
            img_dir = os.path.join(image_base_path, name.lower(), 'image')

            for item in data:
                current_texts.append(item['text'])
                # 假设 image_id 为 12345，路径为 .../image/12345.jpg
                current_image_paths.append(os.path.join(img_dir, f"{item['image_id']}.jpg"))

            dataset_lengths[name] = len(current_texts)
            all_texts.extend(current_texts)
            all_image_paths.extend(current_image_paths)
            print(f"Loaded {len(current_texts)} samples from {name}.")

        except FileNotFoundError:
            print(f"Error: Dataset file not found at {data_file_path}. Skipping.")
            dataset_lengths[name] = 0

    if not all_texts:
        raise RuntimeError("所有数据集均未加载成功或为空。")

    return all_texts, all_image_paths, dataset_lengths


# 辅助函数：将 t-SNE 坐标数组转换为 JSON 格式
def format_tsne_coords(coords_array: np.ndarray):
    return [{'x': float(x), 'y': float(y)} for x, y in coords_array]


# ============================
# 4. 主函数 (整合所有逻辑)
# ============================

def process_multidataset_tsne_multimodal(dataset_names: list, layers_to_extract: list,
                                         output_dir="tsne_multimodal_qwen_output"):
    """
    计算多个数据集的多模态 t-SNE 并进行绘图和保存。
    """
    if len(dataset_names) > len(DATASET_COLORS):
        raise ValueError(f"当前配置最多支持 {len(DATASET_COLORS)} 个数据集。")

    # 1. 加载数据
    texts, image_paths, dataset_lengths = load_and_prepare_data_multimodal(
        dataset_names,
        data_base_path='tsne_output/',  # 假设 JSON 文件在当前运行目录
        image_base_path='/mnt/sda/zzh/verl/data'  # 保持原有图片路径结构
    )

    # 2. 提取所有层 Embedding
    total_samples = len(texts)
    # 存储结果：key 是层索引，value 是该层所有文本的 embedding 列表
    all_embeddings_by_layer = {layer: [] for layer in layers_to_extract}

    for txt, img_path in tqdm(zip(texts, image_paths), total=total_samples, desc="Extracting Multimodal Embeddings"):
        layer_embeddings = get_multimodal_layers_embeddings(
            txt,
            img_path,
            MODEL,
            PROCESSOR,
            layers_to_extract
        )

        for layer_idx, emb in layer_embeddings.items():
            all_embeddings_by_layer[layer_idx].append(emb)

    # 转换为 NumPy 数组
    for layer in layers_to_extract:
        all_embeddings_by_layer[layer] = np.array(all_embeddings_by_layer[layer])

    # 3. 准备标签和颜色

    colors_list = []
    legend_elements = []
    data_start_indices = {}  # 记录每个数据集在最终 X_tsne 中的起始索引
    current_start = 0

    # 为每个数据集创建标签、颜色和图例元素
    for i, name in enumerate(dataset_names):
        count = dataset_lengths.get(name, 0)
        if count > 0:
            color = DATASET_COLORS[i]
            colors_list.extend([color] * count)
            data_start_indices[name] = (current_start, current_start + count)
            current_start += count

            from matplotlib.lines import Line2D
            legend_elements.append(
                Line2D([0], [0], marker='o', color='w', label=name, markerfacecolor=color, markersize=8)
            )

    # 4. 绘图和保存

    os.makedirs(output_dir, exist_ok=True)
    print(f"Outputs will be saved to: {output_dir}/")

    model_name_short = MODEL_NAME.split('/')[-1]

    for layer_idx in layers_to_extract:
        print(f"\n--- Processing Layer {layer_idx} ---")

        embeddings = all_embeddings_by_layer[layer_idx]

        # t-SNE 降维
        print("Starting t-SNE reduction...")
        tsne = TSNE(n_components=2, perplexity=30, random_state=42, n_jobs=-1)
        X_tsne = tsne.fit_transform(embeddings)

        # 绘图
        plt.figure(figsize=(10, 8))

        plt.scatter(X_tsne[:, 0], X_tsne[:, 1], c=colors_list, alpha=0.6)

        plt.legend(handles=legend_elements)

        title = f"t-SNE of Multimodal Embeddings (Qwen {layer_idx}) - {' vs '.join(dataset_names)}"
        plt.title(title)

        # 保存图片
        plot_name = '_'.join(dataset_names).lower()
        plot_filename = os.path.join(output_dir, f'tsne_multimodal_{plot_name}_layer{layer_idx}.png')
        plt.savefig(plot_filename)
        print(f"Plot saved to {plot_filename}")
        plt.close()

        # 保存 t-SNE 坐标值到文件
        for name in dataset_names:
            start, end = data_start_indices.get(name, (0, 0))
            if start < end:
                X_tsne_data = X_tsne[start:end]
                coords_list = format_tsne_coords(X_tsne_data)

                output_filename = os.path.join(output_dir, f'{name.lower()}_tsne_multimodal_layer{layer_idx}.json')
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(coords_list, indent=4, ensure_ascii=False))
                print(f"{name} t-SNE 坐标已保存到 {output_filename}")


# ============================
# 5. 示例运行 (替换了原来的脚本主体)
# ============================

if __name__ == '__main__':
    # 注意：需要确保您的 .json 文件在当前运行目录下，且图片路径正确。
    datasets_to_process = ["CMNER", "WMNER", "GMNER"]
    # datasets_to_process = ["WMNER", "GMNER", "CustomSet"] # 示例：三个数据集
    # ============================
    # 0. 全局配置
    # ============================
    # 定义模型和设备 (保持全局加载)
    MODEL_NAME = "/mnt/sda/zzh/Qwen2.5-VL-7B-Instruct"

    # 定义需要提取的层索引
    TARGET_LAYERS = [28]  # 示例：早层、中层、中高层、顶层 (Qwen-7B可能有32层)

    # 定义用于绘图的颜色列表（最多支持 5 个数据集）
    DATASET_COLORS = ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00']  # Set1 颜色

    # ============================
    # 1. 加载模型 (全局加载一次)
    # ============================
    print(f"Loading model: {MODEL_NAME}...")
    PROCESSOR = AutoProcessor.from_pretrained(MODEL_NAME)
    # 使用 device_map='auto'，让模型自行分配到 GPU
    MODEL = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16,
        device_map='auto'
    )
    process_multidataset_tsne_multimodal(
        dataset_names=datasets_to_process,
        layers_to_extract=TARGET_LAYERS,
        output_dir="tsne_qwen25_mm_output"
    )
