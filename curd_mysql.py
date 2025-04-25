# 手动插入少量数据
from datetime import datetime
import pymysql.cursors


def create_connection(config: dict):
    return pymysql.connect(**config,
                           charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)


def insert_into_table(config, table, data):
    connection = create_connection(config)
    # 通过cursor创建游标
    cursor = connection.cursor()

    query = f"""
    insert into {table} ({', '.join(data.keys())})
    values ({', '.join(data.values())})
    """

    # 插入数据
    try:
        cursor.execute(query)
        connection.commit()
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\tInsert wid {data["wid"]} into {table} successfully.')
    except pymysql.err.Error as e:
        connection.rollback()
        print(e)

    connection.close()



def select_from_table(config, table, columns=None, condition=None):
    connection = create_connection(config)
    cursor = connection.cursor()

    if columns is None:
        keys = '*'
    else:
        keys = ','.join(columns)
    if condition is None:
        query = f"""select {keys} from {table}"""
    else:
        query = f"""select {keys} from {table} where {condition}"""

    try:
        cursor.execute(query)
        data = cursor.fetchall()
        return data
    except pymysql.err.Error as e:
        print(e)

    connection.close()

if __name__ == '__main__':
    import json
    f"""insert into user_id (wid, add_date, del_flag)
            values ('2011445377', NOW(), False)"""

    cnf = json.load(open('./connect_db.json', 'r', encoding='utf-8'))

    # for line in open('./uid_list.txt', 'r', encoding='utf-8').readlines():
    #     if line.strip().isdigit():
    #         d = {
    #             'wid': line.strip(),
    #             'add_date': 'NOW()',
    #         }
    #         insert_into_table(cnf, 'user_id', d)

    d = select_from_table(cnf, 'user_id')
    print(d)
    pass
