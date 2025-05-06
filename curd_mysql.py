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
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\tInsert {data} into {table} successfully.')
    except pymysql.err.Error as e:
        connection.rollback()
        print(e)

    connection.close()


def insert_into_table_transformation(config, table, data):
    connection = create_connection(config)
    cursor = connection.cursor()
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    try:
        cursor.execute(sql, tuple(data.values()))
        connection.commit()
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\tInsert {data} into {table} successfully.')
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


def update_table(config, table, data, condition):
    connection = create_connection(config)
    cursor = connection.cursor()
    set_clause = ', '.join([f"{key} = %s" for key in data.keys()])

    # 构建WHERE条件
    where_clause = ' AND '.join([f"{key} = %s" for key in condition.keys()])

    # 完整的SQL语句
    sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

    # 合并参数值 (SET值在前，WHERE值在后)
    params = tuple(list(data.values()) + list(condition.values()))

    # 执行更新
    try:
        cursor.execute(sql, params)
        connection.commit()
    except pymysql.err.Error as e:
        print(e)


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

    # d = select_from_table(cnf, 'user_id')
    # print(d)
    # d = {
    #     'tweet_id': '1916820320893141313',
    #     'add_date': 'NOW()',
    # }
    # insert_into_table(cnf, 'tweet_id', d)

    # d = select_from_table(cnf, 'user', columns=['id'])

    update_table(cnf, 'tweet_id', {'fetched_flag': 1}, {'tweet_id': '1916820320893141313'})
    pass
