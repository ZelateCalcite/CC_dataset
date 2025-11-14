import json
import re


def clean_weibo_texts(data):
    cleaned_data = []

    for item in data:
        text = item["text"]
        entities = item.get("results", [])

        # 原始文本长度
        orig_len = len(text)

        # 定义要清理的常见噪声模式（可按需扩展）
        # 包含“原图”、"[组图共X张]"、“网页链接”等微博常见结尾
        patterns = [
            r"(\s*\[组图共\d+张\]\s*原图\s*)",
            r"(原图\s*)",
            r"(网页链接\s*)",
            # r"(http[s]?://\S+)",
            r"(展开全文\s*)",
            "\xa0"
        ]

        cleaned_text = text

        # 循环检测，直到没有任何pattern匹配到末尾
        while True:
            modified = False
            for pat in patterns:
                m = re.search(pat + r"$", cleaned_text)
                if m:
                    if m.start() == 0:
                        break
                    cleaned_text = cleaned_text[:m.start()].rstrip()
                    modified = True
                    break  # 删除一次后重新从头开始
            if not modified:
                break

        # 去除多余空格
        cleaned_text = cleaned_text.strip()

        # 若文本被截断，调整标注索引
        diff = len(text) - len(cleaned_text)
        if diff > 0:
            # 若标注超出新的文本长度，截断
            for ent in entities:
                if ent["end"] > len(cleaned_text):
                    ent["end"] = len(cleaned_text)
                    print(item['text'])
                    print(item)
                if ent["start"] > len(cleaned_text):
                    ent["start"] = len(cleaned_text)
                    print(item['text'])

                # 防止出现负值
                ent["start"] = max(ent["start"], 0)
                ent["end"] = max(ent["end"], 0)

        # 写入结果
        cleaned_item = {
            "weibo_id": item["weibo_id"],
            "text": cleaned_text,
            "image": item["image"],
            "results": entities
        }
        cleaned_data.append(cleaned_item)

    return cleaned_data


def check_duplicate_texts(data):
    """
    检查列表中是否存在 text 完全相同的项。
    若存在，打印对应的 weibo_id。
    """
    text_map = {}  # 用于记录已出现过的文本
    duplicates = []  # 记录重复项 weibo_id

    for item in data:
        text = item.get("text", "").strip()
        wid = item.get("weibo_id", "")

        if text in text_map and text not in ['原图', '分享图片']:
            # 若该文本已出现过，则记录重复的 weibo_id
            print(f"重复文本：{wid} 和 {text_map[text]} 内容完全相同\t{text}")
            duplicates.append((text_map[text], wid))
        else:
            text_map[text] = wid

    if not duplicates:
        print("未发现重复文本。")
    else:
        print(f"共发现 {len(duplicates)} 组重复文本。")

    return duplicates


# 示例用法
if __name__ == "__main__":
    with open("labeled_res_special.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    cleaned = clean_weibo_texts(raw_data)

    with open("wmner_clean_special.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    cd = check_duplicate_texts(cleaned)
