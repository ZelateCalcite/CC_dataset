import json

# === 1. 读取原始数据 ===
input_path = 'wmner_clean_special.json'
output_path = 'label_studio_import_gmner_special.json'

with open(input_path, 'r', encoding='utf-8') as f:
    ner_data = json.load(f)

prefix = '/data/local-files/?d='
tasks = []

# === 2. 转换为 Label Studio 导入格式 ===
for item in ner_data:
    if not item['results']:
        continue
    image_path = item.get('image', '')
    if not image_path.startswith(prefix):
        image_path = prefix + image_path

    results = item.get('results', [])

    # 初始化三个字段
    per, loc, org, misc = [], [], [], []

    # 遍历 NER 标注结果，根据 type 填入不同字段
    for r in results:
        ent_text = r.get('text', '').strip()
        ent_type = r.get('type', '').upper()

        if ent_type == 'PER':
            per.append({"value": ent_text})
        elif ent_type == 'LOC':
            loc.append({"value": ent_text})
        elif ent_type == 'ORG':
            org.append({"value": ent_text})
        elif ent_type == 'MISC':
            misc.append({"value": ent_text})
        else:
            # 未知类型可忽略或记录
            pass

    # 构建最终数据结构
    task = {
        "data": {
            "image": image_path,
            "text": item['text'],
            "per": per,
            "loc": loc,
            "org": org,
            "misc": misc
        },
        "meta": item
    }
    tasks.append(task)

# === 3. 写出结果 ===
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(json.dumps(tasks, ensure_ascii=False, indent=2))
