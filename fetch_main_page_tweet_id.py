import re
from random import seed
from time import sleep
from selenium.webdriver import Chrome
from time import sleep, time, strptime, mktime
from random import randint, seed
from datetime import datetime
from curd_mysql import insert_into_table, select_from_table
from selenium import webdriver


def fetch_tweet_id(config, table, diff_list):
    seed(time())

    proxy_ip = "127.0.0.1"
    proxy_port = "30000"

    options = webdriver.ChromeOptions()
    options.add_argument('--proxy-server=http://{}:{}'.format(proxy_ip, proxy_port))
    options.add_argument(r'--user-data-dir=C:\Users\Administrator\AppData\Local\Google\Chrome\User Data')
    options.add_argument("--profile-directory=Profile 2")
    driver = webdriver.Chrome(options=options)
    driver.get("https://x.com/home")
    sleep(10)

    first_scroll = randint(60, 100)
    driver.execute_script(f"window.scrollBy(0, {first_scroll});")
    sleep(randint(50, 1000) * 0.001)
    # driver.execute_script("window.scrollTo(0, 0);")

    total_time = 0
    limit_time = (5 + randint(0, 5)) * 60
    while total_time < limit_time:
        urls = [x.get_attribute('href') for x in driver.find_elements('xpath', "//*[@href]")]
        urls = [i for i in filter(lambda x: re.match(r'.*/status/\d{19}/.*', x), urls)]
        for url in urls:
            try:
                for tid in url.split("/"):
                    if tid.isdigit() and len(tid) == 19 and tid not in diff_list:
                        insert_into_table(config, table, {
                            'tweet_id': tid,
                            'add_date': 'NOW()',
                        })
                        diff_list.add(tid)
            except Exception as e:
                print(e)

        if randint(0, 1):
            total_time += 10
            sleep(10)
        cur_sleep = randint(1, 5)
        total_time += cur_sleep
        sleep(cur_sleep)

        cur_scroll = randint(500, 1200)
        driver.execute_script(f"window.scrollBy(0, {cur_scroll});")
        total_time += 1
        sleep(1)
        print(f'{total_time}\t/\t{limit_time}\tUID LENGTH:\t{len(diff_list)}')
    driver.quit()
    return list(diff_list)


if __name__ == '__main__':
    import json

    cnf = json.load(open('./connect_db.json', 'r', encoding='utf-8'))

    end_time = mktime(strptime('2025-04-30 21:56:41', '%Y-%m-%d %H:%M:%S'))
    total_time = time()
    global_sleep = 3600 + randint(60, 600)

    while end_time > time():
        if time() - total_time > global_sleep:
            temp = randint(1200, 1800)
            print(f'Global Sleep {temp} seconds')
            sleep(temp)
            total_time = time()
            global_sleep = 3600 + randint(60, 600)

        history_data = select_from_table(cnf, 'tweet_id')
        prev_list = set()
        for row in history_data:
            prev_list.add(row['tweet_id'])

        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\t\tCurrent Tweet ID:\t{len(prev_list)}')

        try:
            fetch_tweet_id(cnf, 'tweet_id', prev_list)
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
