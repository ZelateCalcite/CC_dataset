import random

from tqdm import tqdm

SEED = 42
random.seed(SEED)


def construct_template(row):
    from os.path import exists, join
    pbt = ''.join(row['publish_time'].split('T')[0].split('-'))
    filename = f"""{pbt}_{row['weibo_id']}"""
    suffix = '.jpg'
    paths = ['weibo', row['user_id'], 'img', '原创微博图片']
    if exists(join('D:\Code\CC_dataset', *paths, filename + suffix)):
        absolute_path = join('D:\Code\CC_dataset', *paths, filename + suffix)
    else:
        filename += '_1'
        absolute_path = join('D:\Code\CC_dataset', *paths, filename + suffix)
    assert exists(absolute_path), f"{row['weibo_id']}: IMG无法查找到"
    file_path = f"""/data/local-files/?d=CC_dataset/weibo/{row['user_id']}/img/原创微博图片/{filename}{suffix}"""
    save_label2id = {'B-LOC': 0, 'I-LOC': 1, 'B-ORG': 2, 'I-ORG': 3, 'B-PER': 4, 'I-PER': 5, 'B-MISC': 6, 'I-MISC': 7,
                     'O': 8}
    id2label = {
        v: k for k, v in save_label2id.items()
    }
    import_json = {
        'data': {
            'weibo_id': row['weibo_id'],
            'text': row['text'],
            'think': row['think'],
            'image': file_path,
        },
        'meta': {
            k: v for k, v in row.items()
        },
        'predictions': [
            {
                'model_version': 'Qwen3-1.7B-CMNER-S140',
                'created_by': 'Qwen3-1.7B-CMNER-S140-250819',
                'result': extract_prediction(row['text'], row['annotation'], id2label)
            }
        ]
    }
    return import_json


def extract_prediction(text: str, annotation: str, id2label: dict):
    """
    将标注结果(annotation)解析为label-studio格式的预测输出

    Args:
        text (str): 原始文本
        annotation (str): 以逗号分隔的标签ID序列，如 '8,8,8,1,2,2,8'
        id2label (dict): 标签ID到标签名称的映射，例如 {0:"O",1:"B-LOC",2:"I-LOC",3:"B-PER",...}

    Returns:
        list: 每个实体的标注字典，包含 from_name, to_name, type, value
    """
    if len(annotation) == 0:
        return []
    preds = [int(x) for x in annotation.split(",")]
    result = []
    i = 0
    while i < len(preds):
        label_id = preds[i]
        label_tag = id2label.get(label_id, "O")

        if label_tag.startswith("B-"):  # 开始一个新实体
            entity_type = label_tag[2:]
            start = i
            end = i + 1
            # 向后扩展 I- 实体
            while end < len(preds) and id2label.get(preds[end], "O") == f"I-{entity_type}":
                end += 1

            entity_text = text[start:end]
            result.append({
                "from_name": "label",
                "to_name": "text",
                "type": "labels",
                "value": {
                    "start": start,
                    "end": end,
                    "text": entity_text,
                    "labels": [entity_type]
                }
            })
            i = end
        else:
            i += 1
    return result


def sampler(data_list, n):
    return random.sample(list(data_list), n)


def _calculate_entity_num(annotation):
    annotation = annotation.split(',')
    loc, org, per, misc = annotation.count('0'), annotation.count('2'), annotation.count('4'), annotation.count('6')
    return loc + org + per + misc


def calculate_data_distribution(data_list):
    from collections import Counter
    distribution = Counter()
    for i in data_list:
        if isinstance(i, dict):
            distribution[_calculate_entity_num(i['annotation'])] += 1

    print(f'模型标注数量:\t{len(data_list)}')
    for i in sorted(list(distribution.keys())):
        print(f'实体数:\t{i}\t句子数:\t{distribution[i]}')
    return distribution


if __name__ == '__main__':
    import json
    import pymysql.cursors

    config = json.load(open('./connect_db.json', 'r', encoding='utf-8'))

    connection = pymysql.connect(**config,
                                 charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    query = f"""select * from weibo_pre_annotation where import_status = 0 and del_flag = 0"""

    try:
        cursor.execute(query)
        ann_data = cursor.fetchall()
    except pymysql.err.Error as e:
        ann_data = None
        print(e)

    connection.close()

    # target = {0: random.randint(200, 800), 1: random.randint(3000, 4000), 2: random.randint(6000, 7000)}
    target = {0: 700, 1: 3500, 2: 6500}
    results = {}
    filtered = {k: [] for k in target}
    for d in ann_data:
        ent_num = _calculate_entity_num(d['annotation'])
        if filtered.get(ent_num) is not None:
            filtered[ent_num].append(d)
    for k, v in filtered.items():
        results[k] = sampler(v, target[k])

    seq = []
    sql_update_list = []
    err_list = []
    pbar = tqdm(total=sum(target.values()))
    for d in results.values():
        for item in d:
            wid = item['weibo_id']
            connection = pymysql.connect(**config,
                                         charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
            cursor = connection.cursor()
            query = f"""select user_id, content, publish_time from weibo where id = '{wid}'"""

            try:
                cursor.execute(query)
                temp = cursor.fetchall()
            except pymysql.err.Error as e:
                temp = None
                print(e)

            connection.close()
            item['user_id'] = temp[0]['user_id']
            item['text'] = temp[0]['content']
            item['publish_time'] = temp[0]['publish_time'].strftime("%Y-%m-%dT%H:%M:%S")
            item['add_date'] = item['add_date'].strftime("%Y-%m-%dT%H:%M:%S")

            try:
                json_data = construct_template(item)
            except AssertionError as e:
                # print(e)
                err_list.append(wid)
                pbar.update(1)
                continue
            sql_update_list.append(wid)
            seq.append(json_data)
            pbar.update(1)
    with open('./import_20250822.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(seq, ensure_ascii=False))
    with open('./update_db.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(sql_update_list, ensure_ascii=False))

    pass
