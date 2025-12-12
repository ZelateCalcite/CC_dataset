import json
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
import torch
import os


# ============================
# 2. 批量 embedding 提取函数 (保持不变)
# ============================
def get_all_layers_embeddings(texts: list, model, tokenizer, device, layers_to_extract: list):
    """
    对所有文本进行推理，并提取指定层的所有 embedding。
    """
    all_embeddings_by_layer = {layer: [] for layer in layers_to_extract}

    for text in tqdm(texts, desc="Extracting embeddings across layers"):
        inputs = tokenizer(text, return_tensors="pt").to(device)

        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True)

        hidden_states = outputs.hidden_states

        for layer_idx in layers_to_extract:
            if layer_idx < len(hidden_states):
                layer_output = hidden_states[layer_idx]
                embedding = layer_output.mean(dim=1).cpu().numpy()[0]
                all_embeddings_by_layer[layer_idx].append(embedding)
            else:
                raise ValueError(f"Model does not have layer index {layer_idx}. Max index is {len(hidden_states) - 1}")

    for layer in layers_to_extract:
        all_embeddings_by_layer[layer] = np.array(all_embeddings_by_layer[layer])

    return all_embeddings_by_layer


# ============================
# 3. 数据处理辅助函数 (新增)
# ============================

def load_and_prepare_data(dataset_names: list, base_path="./"):
    """
    加载指定的数据集，合并文本，并记录每个数据集的长度。
    """
    if len(dataset_names) > 5:
        raise ValueError("最多支持 5 个数据集进行同时计算。")

    all_texts = []
    dataset_lengths = {}  # 存储 {name: length}

    # 路径格式假设为 {base_path}/{name}.json
    for name in dataset_names:
        file_path = os.path.join(base_path, f'{name.lower()}.json')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            current_texts = [item["text"] for item in data]
            dataset_lengths[name] = len(current_texts)
            all_texts.extend(current_texts)
            print(f"Loaded {len(current_texts)} samples from {name}.")

        except FileNotFoundError:
            print(f"Error: Dataset file not found at {file_path}. Skipping.")
            dataset_lengths[name] = 0

    if not all_texts:
        raise RuntimeError("所有数据集均未加载成功或为空。")

    return all_texts, dataset_lengths


# 辅助函数：将 t-SNE 坐标数组转换为 JSON 格式
def format_tsne_coords(coords_array: np.ndarray):
    return [{'x': float(x), 'y': float(y)} for x, y in coords_array]


# ============================
# 4. 主函数 (整合所有逻辑)
# ============================

def process_multidataset_tsne(dataset_names: list, layers_to_extract: list, output_dir="tsne_outputs"):
    """
    计算多个数据集的 t-SNE 并进行绘图和保存。
    """
    if len(dataset_names) > len(DATASET_COLORS):
        raise ValueError(f"当前配置最多支持 {len(DATASET_COLORS)} 个数据集。")

    # 1. 加载数据
    texts, dataset_lengths = load_and_prepare_data(dataset_names, base_path='tsne_output/')

    # 2. 提取 Embedding
    all_embeddings_dict = get_all_layers_embeddings(
        texts,
        MODEL,  # 使用全局加载的模型
        TOKENIZER,
        DEVICE,
        layers_to_extract
    )

    # 3. 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    print(f"Outputs will be saved to: {output_dir}/")

    # 4. 准备标签和颜色
    current_idx = 0
    labels = []
    colors_list = []
    legend_elements = []

    # 为每个数据集创建标签、颜色和图例元素
    for i, name in enumerate(dataset_names):
        count = dataset_lengths.get(name, 0)
        if count > 0:
            color = DATASET_COLORS[i]
            labels.extend([name] * count)
            colors_list.extend([color] * count)

            from matplotlib.lines import Line2D
            legend_elements.append(
                Line2D([0], [0], marker='o', color='w', label=name, markerfacecolor=color, markersize=8)
            )

    # 5. 循环计算 t-SNE、绘图和保存

    data_start_indices = {}  # 记录每个数据集在最终 X_tsne 中的起始索引
    current_start = 0
    for name in dataset_names:
        length = dataset_lengths.get(name, 0)
        if length > 0:
            data_start_indices[name] = (current_start, current_start + length)
            current_start += length

    for layer_idx in layers_to_extract:
        print(f"\n--- Processing Layer {layer_idx} ---")

        embeddings = all_embeddings_dict[layer_idx]

        # t-SNE 降维
        print("Starting t-SNE reduction...")
        tsne = TSNE(n_components=2, perplexity=30, random_state=42, n_jobs=-1)
        X_tsne = tsne.fit_transform(embeddings)

        # 绘图
        plt.figure(figsize=(10, 8))

        # 按照标签顺序绘图，确保颜色对应
        plt.scatter(X_tsne[:, 0], X_tsne[:, 1], c=colors_list, alpha=0.6)

        plt.legend(handles=legend_elements)

        title = f"t-SNE of Qwen Layer {layer_idx} Embeddings ({' vs '.join(dataset_names)})"
        plt.title(title)

        # 保存图片
        plot_name = '_'.join(dataset_names).lower()
        plot_filename = os.path.join(output_dir, f'tsne_{plot_name}_layer{layer_idx}.png')
        plt.savefig(plot_filename)
        print(f"Plot saved to {plot_filename}")
        plt.close()

        # 保存 t-SNE 坐标值到文件
        for name in dataset_names:
            start, end = data_start_indices.get(name, (0, 0))
            if start < end:
                X_tsne_data = X_tsne[start:end]
                coords_list = format_tsne_coords(X_tsne_data)

                output_filename = os.path.join(output_dir, f'{name.lower()}_tsne_layer{layer_idx}.json')
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(coords_list, ensure_ascii=False))
                print(f"{name} t-SNE 坐标已保存到 {output_filename}")


# ============================
# 5. 示例运行 (替换了原来的脚本主体)
# ============================

if __name__ == '__main__':
    # 示例运行：输入数据集名称的列表 (最多 5 个)
    # 假设文件名为 gmner.json, wmner.json, etc.
    datasets_to_process = ["CMNER", "GMNER", "WMNER"]
    # datasets_to_process = ["GMNER", "WMNER", "datasetC"] # 示例：三个数据集
    # 定义需要提取的层索引
    TARGET_LAYERS = [28]
    # ============================
    # 0. 配置
    # ============================
    # 定义模型和设备 (保持全局或作为参数传递)
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    MODEL_NAME = "/home/zzh/baselines/Qwen2.5-VL-7B-Instruct"

    # 定义用于绘图的颜色列表（最多支持 5 个数据集）
    DATASET_COLORS = ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00']  # Set1 颜色

    # ============================
    # 1. 加载模型 (全局加载一次)
    # ============================
    print(f"Loading model: {MODEL_NAME}...")
    TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)
    MODEL = AutoModel.from_pretrained(MODEL_NAME, torch_dtype=torch.float16).to(DEVICE)

    process_multidataset_tsne(
        dataset_names=datasets_to_process,
        layers_to_extract=TARGET_LAYERS,
        output_dir="tsne_qwen25_text_only_output"
    )
