import json
import pymysql.cursors

config = json.load(open('./connect_db.json', 'r', encoding='utf-8'))

connection = pymysql.connect(**config,
                             charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()
for i in json.load(open('./update_db.json', 'r', encoding='utf-8')):
    query = f"""UPDATE weibo_pre_annotation SET import_status = 1 where weibo_id = '{i}' and del_flag = 0;"""

    try:
        cursor.execute(query)
        connection.commit()
    except pymysql.err.Error as e:
        connection.rollback()
        print(e)

connection.close()
