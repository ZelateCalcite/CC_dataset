import json
from tqdm import tqdm
from curd_mysql import select_from_table

cnf = json.load(open('./connect_db.json', 'r', encoding='utf-8'))

id2weibo = json.load(open('./wmner_id_index.json', 'r', encoding='utf-8'))
for split in ['train', 'val', 'test']:
    tokens = 0
    images = 0
    data = json.load(open(f'./wmner/{split}.json', 'r', encoding='utf-8'))
    total = len(data)
    for d in tqdm(data):
        weibo_id = id2weibo[str(d['id'])]
        source = select_from_table(cnf, 'weibo', columns=['original_pictures'], condition=f'id = \'{weibo_id}\'')
        image_list = source[0]['original_pictures'].split(',')
        if len(image_list) == 1:
            images += len(image_list)
        else:
            images += 2
        tokens += len(d['text'])
    print(f'{split}\t{total}\t{tokens}\t{images}')
    pass
