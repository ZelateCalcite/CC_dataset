import json
import re

# === 1. 读取 Label Studio 导出的 JSON 文件 ===
input_path = r'C:\Users\Administrator\Downloads\project-1-at-2025-10-29-06-22-6d038061.json'
with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === 2. 遍历每条样本，解析 data 与 result ===
parsed = []
for item in data:
    # ---- 基础字段 ----
    weibo_id = item['data'].get('weibo_id', '')
    text = item['data'].get('text', '')
    image_url = item['data'].get('image', '')
    image_url = re.sub(r'/data/local-files/\?d=', '', image_url)

    # ---- 解析标注结果 result ----
    results = []
    for res in item.get('annotations', []):
        # 有些文件结构是 item['annotations']，有些是 item['completions']
        if 'result' not in res:
            continue
        for r in res['result']:
            value = r.get('value', {})
            label = None
            start = end = None
            text_span = None

            # 文本标注（例如命名实体、情感等）
            if 'labels' in value:
                label = value['labels'][0] if value['labels'] else None
            if 'start' in value and 'end' in value:
                start, end = value['start'], value['end']
                text_span = value.get('text', text[start:end])

            if label is not None:
                if start > 0 and end < len(text):
                    if (text[start - 1] == '<' and text[end] == '>') or (text[start - 1] == '《' and text[end] == '》'):
                        start -= 1
                        end += 1
                        text_span = text[start:end]
                results.append({
                    'type': label,
                    'text': text_span,
                    'start': start,
                    'end': end
                })

    parsed.append({
        'weibo_id': weibo_id,
        'text': text,
        'image': image_url,
        'results': results
    })

with open('./labeled_res.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(list(filter(lambda x: len(x['results']) < 15, parsed)), ensure_ascii=False, indent=2))
