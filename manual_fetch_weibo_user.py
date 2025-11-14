from selenium.webdriver import Chrome
from time import sleep, time, mktime, strptime
from random import randint, seed
from datetime import datetime
from curd_mysql import insert_into_table, select_from_table


# save to txt
def fetch_uid(config, table, diff_list, web):
    uid_list = diff_list
    elements = web.find_elements('class name', 'ALink_default_2ibt1')
    elements = list(filter(lambda x: x.tag_name == "a" and x.text == '', elements))
    for el in elements:
        try:
            attribute = el.get_attribute("href")
            uid = attribute.split("/")[-1]
            if uid.isdigit() and uid not in uid_list:
                insert_into_table(config, table, {
                    'wid': uid,
                    'add_date': 'NOW()',
                })
                uid_list.add(uid)
        except Exception as e:
            print(e)
    return list(uid_list)


if __name__ == "__main__":
    import json
    cnf = json.load(open('./connect_db.json', 'r', encoding='utf-8'))
    client = Chrome()
    client.get("https://www.weibo.com")

    history_data = select_from_table(cnf, 'user_id')
    prev_list = set()
    for row in history_data:
        prev_list.add(row['wid'])

    while mktime(strptime('2025-05-12 12:36:41', '%Y-%m-%d %H:%M:%S')) > time():
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\t\tCurrent UID:\t{len(prev_list)}')
        print('Recording')
        try:
            fetch_uid(cnf, 'user_id', prev_list, client)
        except Exception as err:
            print(err)
            continue
        print('Waiting 5 seconds...')
        sleep(5)
    client.quit()

    pass
