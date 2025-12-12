import json
from collections import defaultdict
import matplotlib.pyplot as plt


def print_dataset_analysis(parsed, label_name='results'):
    # parsed = json.load(open('./wmner_clean.json', 'r', encoding='utf-8'))

    type_count = defaultdict(int)  # 各类型总数量
    sample_type_count = defaultdict(list)  # 每种类型对应的每条样本数量分布
    total_labels_per_sample = []  # 每条样本总标注数量

    # === 3. 遍历每条样本 ===
    for item in parsed:
        results = item.get(label_name, [])
        total_labels_per_sample.append(len(results))

        # 统计不同type的数量
        per_type_counter = defaultdict(int)
        for r in results:
            r_type = r.get('type', 'unknown')
            type_count[r_type] += 1
            per_type_counter[r_type] += 1

        # 每种type在该样本中出现次数
        for t, c in per_type_counter.items():
            sample_type_count[t].append(c)

    # === 4. 输出总体分析 ===
    print("=== 标注统计结果 ===")
    print(f"总样本数: {len(parsed)}")
    print(f"总标注数: {sum(total_labels_per_sample)}")
    print(f"平均每条样本标注数: {sum(total_labels_per_sample) / len(total_labels_per_sample):.2f}")
    print(f"最大标注数: {max(total_labels_per_sample)}")
    print(f"最小标注数: {min(total_labels_per_sample)}\n")
    zero_labels = sum(1 for n in total_labels_per_sample if n == 0)
    less_than_five = sum(1 for n in total_labels_per_sample if n < 5)

    print("\n=== 标注数量分布 ===")
    print(f"标注数为 0 的样本数量: {zero_labels}")
    print(f"标注数 < 5 的样本数量: {less_than_five}")

    print("=== 按 type 分类统计 ===")
    for t, cnt in type_count.items():
        counts = sample_type_count[t]
        avg = sum(counts) / len(counts) if counts else 0
        print(f"类型: {t:<20} 总数: {cnt:<5} | 出现在 {len(counts)} 条样本 | 每样本平均数量: {avg:.2f}")

    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(figsize=(10, 5))
    plt.bar(range(len(total_labels_per_sample)), total_labels_per_sample, color='skyblue', edgecolor='black')
    plt.title("每个样本的标注数量分布", fontsize=14)
    plt.xlabel("样本索引", fontsize=12)
    plt.ylabel("标注数量", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    # === 3. 绘制每种标注类型(type)的总数量柱状图 ===
    plt.figure(figsize=(8, 5))
    plt.bar(type_count.keys(), type_count.values(), color='salmon', edgecolor='black')
    plt.title("各标注类型的数量分布", fontsize=14)
    plt.xlabel("标注类型 (type)", fontsize=12)
    plt.ylabel("标注总数", fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    # plt.savefig('3.svg', format='svg', dpi=300)
    plt.show()

if __name__ == '__main__':
    import json
    data = json.load(open('./wmner/test.json', 'r', encoding='utf-8'))
    print_dataset_analysis(data, label_name='label')
