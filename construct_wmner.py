import json
import re
import shutil
from os.path import exists, join
from collections import defaultdict, Counter
from process_weibo_anno_plot import print_dataset_analysis
import random

# random shuffle 可控
random.seed(42)


def build_label_buckets(all_data):
    """
    按照每个 item 的 (PER, LOC, ORG, MISC) 数量编码成十六进制 key，
    并构建 buckets 字典。
    """

    # 固定类别顺序
    label_order = ["PER", "LOC", "ORG", "MISC"]

    buckets = defaultdict(list)

    for item in all_data:
        # 统计实体数量
        type_list = [ent["type"] for ent in item.get("label", [])]
        counter = Counter(type_list)

        # 生成十六进制 key（按指定类别顺序编码）
        key = ""
        for t in label_order:
            count = counter.get(t, 0)
            # 转十六进制（去掉'0x'前缀，保持一位）
            key += format(count, "x")  # one hex digit (0-f)

        # 放入 bucket
        buckets[key].append(item)

    return buckets


# --------------------------------------------------
# 假设已有 bucket
# 每个 key 是 "per loc org misc" 的十六进制编码
# value 是 item 列表，每个 item 至少包含 label 类型计数字典，如:
# item = {"text": "...", "labels": {"PER":2, "LOC":1, "ORG":0, "MISC":1}}
# --------------------------------------------------

# 示例：
# buckets = {
#     "1102": [item1, item2, ...],
#     "2000": [...],
# }


def extract_vector_from_code(code):
    return [int(c, 16) for c in code]


def add_vector(a, b):
    return [a[i] + b[i] for i in range(4)]


def sub_vector(a, b):
    return [a[i] - b[i] for i in range(4)]


def vector_score(v):
    return sum(abs(x) for x in v)


def dataset_split(buckets):
    train, val, test = [], [], []

    # 每个 set 的标签向量
    vec_train = [0, 0, 0, 0]
    vec_dev = [0, 0, 0, 0]
    vec_test = [0, 0, 0, 0]

    for code, items in buckets.items():
        vec_code = extract_vector_from_code(code)

        items = items[:]
        random.shuffle(items)

        total = len(items)
        n_train = round(total * 0.7)
        n_dev = round(total * 0.15)
        n_test = total - n_train - n_dev

        group_train = items[:n_train]
        group_dev = items[n_train:n_train + n_dev]
        group_test = items[n_train + n_dev:n_train + n_dev + n_test]
        remain = items[n_train + n_dev + n_test:]

        # --- 按比例添加 ---
        for item in group_train:
            train.append(item)
            vec_train = add_vector(vec_train, vec_code)

        for item in group_dev:
            val.append(item)
            vec_dev = add_vector(vec_dev, vec_code)

        for item in group_test:
            test.append(item)
            vec_test = add_vector(vec_test, vec_code)

        # --- 处理剩余 ---
        for item in remain:
            score_train = vector_score(add_vector(vec_train, vec_code))
            score_dev = vector_score(add_vector(vec_dev, vec_code))
            score_test = vector_score(add_vector(vec_test, vec_code))

            best = min(
                [("train", score_train), ("val", score_dev), ("test", score_test)],
                key=lambda x: x[1]
            )[0]

            if best == "train":
                train.append(item)
                vec_train = add_vector(vec_train, vec_code)
            elif best == "val":
                val.append(item)
                vec_dev = add_vector(vec_dev, vec_code)
            else:
                test.append(item)
                vec_test = add_vector(vec_test, vec_code)

    return {
        "train": train,
        "val": val,
        "test": test,
        "vec_train": vec_train,
        "vec_dev": vec_dev,
        "vec_test": vec_test,
    }


if __name__ == '__main__':
    data = json.load(open('./wmner_clean.json', 'r', encoding='utf-8'))
    data.extend(json.load(open('./wmner_clean_special.json', 'r', encoding='utf-8')))
    data_sorted = sorted(data, key=lambda x: x["weibo_id"])

    # check entity span
    for i in data:
        if i['results']:
            for e in i['results']:
                if i['text'][e['start']: e['end']] != e['text']:
                    print(i['weibo_id'])
                    al = re.finditer(e['text'], i['text'])
                    for j in al:
                        print(j.start(), j.end())

    pass

    all_outputs = []
    files = []
    for i, d in enumerate(data_sorted):
        src = join('D:\\Code\\', d['image'])
        assert exists(src), f"{d['weibo_id']}: IMG无法查找到"
        new_id = i
        temp = {
            "id": new_id,
            "text": d['text'],
            "label": d['results'],
        }
        all_outputs.append(temp)
        files.append({
            "id": new_id,
            "src": src,
        })

    splits = dataset_split(build_label_buckets(all_outputs))
    print_dataset_analysis(splits['train'], label_name='label')
    print_dataset_analysis(splits['val'], label_name='label')
    print_dataset_analysis(splits['test'], label_name='label')

    for f in files:
        tgt = f"D:\\Code\\CC_dataset\\wmner\\image\\{f['id']}.jpg"
        shutil.copy(f['src'], tgt)

    with open('./wmner/train.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(splits['train'], ensure_ascii=False))
    with open('./wmner/val.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(splits['val'], ensure_ascii=False))
    with open('./wmner/test.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(splits['test'], ensure_ascii=False))
    pass
