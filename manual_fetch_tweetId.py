import re
from random import seed
from time import sleep
from selenium.webdriver import Chrome
from time import sleep, time, strptime, mktime
from random import randint, seed
from datetime import datetime
from curd_mysql import insert_into_table, select_from_table
from selenium import webdriver
import json

proxy_ip = "127.0.0.1"
proxy_port = "30000"

options = webdriver.ChromeOptions()
options.add_argument('--proxy-server=http://{}:{}'.format(proxy_ip, proxy_port))
options.add_argument(r'--user-data-dir=C:\Users\Administrator\AppData\Local\Google\Chrome\User Data')
options.add_argument("--profile-directory=Profile 2")
driver = webdriver.Chrome(options=options)
driver.get("https://x.com/home")
sleep(10)

cnf = json.load(open('./connect_db.json', 'r', encoding='utf-8'))

history_data = select_from_table(cnf, 'tweet_id')
prev_list = set()
for row in history_data:
    prev_list.add(row['tweet_id'])

while mktime(strptime('2025-05-01 21:56:41', '%Y-%m-%d %H:%M:%S')) > time():
    try:
        urls = [x.get_attribute('href') for x in driver.find_elements('xpath', "//*[@href]")]
    except Exception as e:
        print(e)
        print('\nRecording\n')
        sleep(5)
        continue
    urls = [i for i in filter(lambda x: re.match(r'.*/status/\d{19}/.*', x), urls)]
    for url in urls:
        try:
            for tid in url.split("/"):
                if tid.isdigit() and len(tid) == 19 and tid not in prev_list:
                    insert_into_table(cnf, 'tweet_id', {
                        'tweet_id': tid,
                        'add_date': 'NOW()',
                    })
                    prev_list.add(tid)
        except Exception as e:
            print(e)
    print('\nSleeping\n')
    sleep(3)
    print('\nRecording\n')