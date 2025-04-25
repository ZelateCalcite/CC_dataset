from selenium.webdriver import Chrome
from time import sleep, time
from random import randint, seed
from datetime import datetime
from curd_mysql import insert_into_table, select_from_table


# save to txt
def fetch_uid(config, table, diff_list):
    seed(time())

    web = Chrome()
    web.get("https://www.weibo.com")
    sleep(5)
    uid_list = diff_list

    first_scroll = randint(60, 100)
    web.execute_script(f"window.scrollBy(0, {first_scroll});")
    sleep(randint(50, 1000) * 0.001)
    web.execute_script("window.scrollTo(0, 0);")

    total_time = 0
    limit_time = (5 + randint(0, 5)) * 60
    while total_time < limit_time:
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

        if randint(0, 1):
            total_time += 10
            sleep(10)
        cur_sleep = randint(1, 5)
        total_time += cur_sleep
        sleep(cur_sleep)

        cur_scroll = randint(200, 700)
        web.execute_script(f"window.scrollBy(0, {cur_scroll});")
        total_time += 1
        sleep(1)
        print(f'{total_time}\t/\t{limit_time}\tUID LENGTH:\t{len(uid_list)}')
    web.quit()
    return list(uid_list)


def save_to_mysql(config, uid_list):
    for uid in uid_list:
        insert_into_table(config, 'user_id', {
            'wid': str(uid),
            'add_date': 'NOW()',
        })


if __name__ == "__main__":
    import json
    cnf = json.load(open('./connect_db.json', 'r', encoding='utf-8'))

    end_time = 1745566095
    while end_time > time():
        if 1745476095 > time() > 1745472495:
            print('Waiting 3212')
            sleep(3212)
        history_data = select_from_table(cnf, 'user_id')
        prev_list = set()
        for row in history_data:
            prev_list.add(row['wid'])

        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\t\tCurrent UID:\t{len(prev_list)}')

        try:
            fetch_uid(cnf, 'user_id', prev_list)
        except Exception as err:
            print(err)
            continue

        sleep_time = randint(1, 20) * 60 + randint(0, 120)
        if sleep_time + time() > end_time:
            print('===END===')
            break
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\t\tWait Time:\t{sleep_time}')
        sleep(sleep_time)

    pass
