import json
import random

import pymysql

from import_to_label_studio_ner import construct_template

user_id_list = [i.strip() for i in open('./special_fetch.log').readlines()]

config = json.load(open('./connect_db.json', 'r', encoding='utf-8'))

seq = []

for uid in user_id_list:
    connection = pymysql.connect(**config,
                                 charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    query = f"""select id, content, publish_time, original_pictures from weibo where user_id = '{uid}'"""

    try:
        cursor.execute(query)
        temp = cursor.fetchall()
    except pymysql.err.Error as e:
        temp = None
        print(e)

    connection.close()

    li = []
    for i in temp:
        if len(i['content']) <= 250 and i['original_pictures'] != '无':
            li.append(i)
    if len(li) >= 30:
        li = random.sample(li, 30)
    for i in li:
        t = {k: v for k, v in i.items()}
        t['publish_time'] = t['publish_time'].strftime("%Y-%m-%dT%H:%M:%S")
        t['weibo_id'] = t['id']
        t['user_id'] = uid
        t['think'] = ''
        t['text'] = t['content']
        t['annotation'] = ''
        try:
            data_json = construct_template(t)
            seq.append(data_json)
        except Exception as e:
            continue
    pass

with open('./import_20251114.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(seq, ensure_ascii=False))
