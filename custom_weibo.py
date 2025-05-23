#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import logging
import logging.config
import os
import random
import shutil
import sys
from datetime import date, datetime, timedelta
from time import sleep

from absl import app, flags
from tqdm import tqdm

from weiboSpider.weibo_spider import config_util, datetime_util
from weiboSpider.weibo_spider.downloader import AvatarPictureDownloader
from weiboSpider.weibo_spider.parser import AlbumParser, IndexParser, PageParser, PhotoParser
from weiboSpider.weibo_spider.user import User

FLAGS = flags.FLAGS

flags.DEFINE_string('config_path', None, 'The path to config.json.')
flags.DEFINE_string('u', None, 'The user_id we want to input.')
flags.DEFINE_string('user_id_list', None, 'The path to user_id_list.txt.')
flags.DEFINE_string('output_dir', None, 'The dir path to store results.')

logging_path = os.path.split(
    os.path.realpath(__file__))[0] + os.sep + 'logging.conf'
logging.config.fileConfig(logging_path)
logger = logging.getLogger('spider')

global_config = {
    "user_id_list": [],
    "filter": 1,
    "since_date": "2024-01-01",
    "end_date": "2024-12-31",
    "random_wait_pages": [1, 5],
    "random_wait_seconds": [6, 10],
    "global_wait": [[1000, 3600], [500, 2000]],
    "write_mode": ["csv", "txt", "json"],
    "pic_download": 1,
    "video_download": 0,
    "file_download_timeout": [5, 5, 10],
    "result_dir_name": 1,
    "cookie": "SCF=AkmHhln62YDWFSFl1vzulQ-Wd09yddy7K-VnCJTtefEZwQpHyTQ8rcB-6LO65zIESqUfTmwTKhnxkYr2kee1cLk.; SUB=_2A25K9_PVDeRhGeFH6FYT8ibLwj2IHXVpjQkdrDV6PUJbktANLUPAkW1Ne36qaB-BH-V5wti5RpbFJ5Gb6fAjFDg0; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFRqula4izcRzF_cgpYMsE.5NHD95QN1KeXeozRS0.pWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0.0ShzE1hM4eBtt; SSOLoginState=1744012165; ALF=1746604165",
}


class Spider:
    def __init__(self, config):
        """Weibo类初始化"""
        self.filter = config[
            'filter']  # 取值范围为0、1,程序默认值为0,代表要爬取用户的全部微博,1代表只爬取用户的原创微博
        since_date = config['since_date']
        if isinstance(since_date, int):
            since_date = date.today() - timedelta(since_date)
        self.since_date = str(
            since_date)  # 起始时间，即爬取发布日期从该值到结束时间的微博，形式为yyyy-mm-dd
        self.end_date = config[
            'end_date']  # 结束时间，即爬取发布日期从起始时间到该值的微博，形式为yyyy-mm-dd，特殊值"now"代表现在
        random_wait_pages = config['random_wait_pages']
        self.random_wait_pages = [
            min(random_wait_pages),
            max(random_wait_pages)
        ]  # 随机等待频率，即每爬多少页暂停一次
        random_wait_seconds = config['random_wait_seconds']
        self.random_wait_seconds = [
            min(random_wait_seconds),
            max(random_wait_seconds)
        ]  # 随机等待时间，即每次暂停要sleep多少秒
        self.global_wait = config['global_wait']  # 配置全局等待时间，如每爬1000页等待3600秒等
        self.page_count = 0  # 统计每次全局等待后，爬取了多少页，若页数满足全局等待要求就进入下一次全局等待
        self.write_mode = config[
            'write_mode']  # 结果信息保存类型，为list形式，可包含txt、csv、json、mongo和mysql五种类型
        self.pic_download = config[
            'pic_download']  # 取值范围为0、1,程序默认值为0,代表不下载微博原始图片,1代表下载
        self.video_download = config[
            'video_download']  # 取值范围为0、1,程序默认为0,代表不下载微博视频,1代表下载
        self.file_download_timeout = config.get(
            'file_download_timeout',
            [5, 5, 10
             ])  # 控制文件下载“超时”时的操作，值是list形式，包含三个数字，依次分别是最大超时重试次数、最大连接时间和最大读取时间
        self.result_dir_name = config.get(
            'result_dir_name', 0)  # 结果目录名，取值为0或1，决定结果文件存储在用户昵称文件夹里还是用户id文件夹里
        self.cookie = config['cookie']
        self.mysql_config = config.get('mysql_config')  # MySQL数据库连接配置，可以不填

        self.sqlite_config = config.get('sqlite_config')
        self.kafka_config = config.get('kafka_config')
        self.mongo_config = config.get('mongo_config')
        self.post_config = config.get('post_config')
        self.user_config_file_path = ''
        user_id_list = config['user_id_list']
        if FLAGS.user_id_list:
            user_id_list = FLAGS.user_id_list
        if not isinstance(user_id_list, list):
            if not os.path.isabs(user_id_list):
                user_id_list = os.getcwd() + os.sep + user_id_list
            if not os.path.isfile(user_id_list):
                logger.warning('不存在%s文件', user_id_list)
                sys.exit()
            self.user_config_file_path = user_id_list
        if FLAGS.u:
            user_id_list = FLAGS.u.split(',')
        if isinstance(user_id_list, list):
            # 第一部分是处理dict类型的
            # 第二部分是其他类型,其他类型提供去重功能
            user_config_list = list(
                map(
                    lambda x: {
                        'user_uri': x['id'],
                        'since_date': x.get('since_date', self.since_date),
                        'end_date': x.get('end_date', self.end_date),
                    }, [
                        user_id for user_id in user_id_list
                        if isinstance(user_id, dict)
                    ])) + list(
                map(
                    lambda x: {
                        'user_uri': x,
                        'since_date': self.since_date,
                        'end_date': self.end_date
                    },
                    set([
                        user_id for user_id in user_id_list
                        if not isinstance(user_id, dict)
                    ])))
            if FLAGS.u:
                config_util.add_user_uri_list(self.user_config_file_path,
                                              user_id_list)
        else:
            user_config_list = config_util.get_user_config_list(
                user_id_list, self.since_date)
            for user_config in user_config_list:
                user_config['end_date'] = self.end_date
        self.user_config_list = user_config_list  # 要爬取的微博用户的user_config列表
        self.user_config = {}  # 用户配置,包含用户id和since_date
        self.new_since_date = ''  # 完成某用户爬取后，自动生成对应用户新的since_date
        self.user = User()  # 存储爬取到的用户信息
        self.got_num = 0  # 存储爬取到的微博数
        self.weibo_id_list = []  # 存储爬取到的所有微博id

    def write_weibo(self, weibos):
        """将爬取到的信息写入文件或数据库"""
        for writer in self.writers:
            writer.write_weibo(weibos)
        for downloader in self.downloaders:
            downloader.download_files(weibos)

    def write_user(self, user):
        """将用户信息写入数据库"""
        for writer in self.writers:
            writer.write_user(user)

    def get_user_info(self, user_uri):
        """获取用户信息"""
        self.user = IndexParser(self.cookie, user_uri).get_user()
        self.page_count += 1

    def download_user_avatar(self, user_uri):
        """下载用户头像"""
        avatar_album_url = PhotoParser(self.cookie,
                                       user_uri).extract_avatar_album_url()
        pic_urls = AlbumParser(self.cookie,
                               avatar_album_url).extract_pic_urls()
        AvatarPictureDownloader(
            self._get_filepath('img'),
            self.file_download_timeout).handle_download(pic_urls)

    def get_weibo_info(self):
        """获取微博信息"""
        try:
            since_date = datetime_util.str_to_time(
                self.user_config['since_date'])
            now = datetime.now()
            if since_date <= now:
                page_num = IndexParser(
                    self.cookie,
                    self.user_config['user_uri']).get_page_num()  # 获取微博总页数
                self.page_count += 1
                if self.page_count > 2 and (self.page_count +
                                            page_num) > self.global_wait[0][0]:
                    wait_seconds = int(
                        self.global_wait[0][1] *
                        min(1, self.page_count / self.global_wait[0][0]))
                    logger.info(u'即将进入全局等待时间，%d秒后程序继续执行' % wait_seconds)
                    for i in tqdm(range(wait_seconds)):
                        sleep(1)
                    self.page_count = 0
                    self.global_wait.append(self.global_wait.pop(0))
                page1 = 0
                random_pages = random.randint(*self.random_wait_pages)
                for page in tqdm(range(1, page_num + 1), desc='Progress'):
                    weibos, self.weibo_id_list, to_continue = PageParser(
                        self.cookie,
                        self.user_config, page, self.filter).get_one_page(
                        self.weibo_id_list)  # 获取第page页的全部微博
                    logger.info(
                        u'%s已获取%s(%s)的第%d页微博%s',
                        '-' * 30,
                        self.user.nickname,
                        self.user.id,
                        page,
                        '-' * 30,
                    )
                    self.page_count += 1
                    if weibos:
                        yield weibos
                    if not to_continue:
                        break

                    # 通过加入随机等待避免被限制。爬虫速度过快容易被系统限制(一段时间后限
                    # 制会自动解除)，加入随机等待模拟人的操作，可降低被系统限制的风险。默
                    # 认是每爬取1到5页随机等待6到10秒，如果仍然被限，可适当增加sleep时间
                    if (page - page1) % random_pages == 0 and page < page_num:
                        sleep(random.randint(*self.random_wait_seconds))
                        page1 = page
                        random_pages = random.randint(*self.random_wait_pages)

                    if self.page_count >= self.global_wait[0][0]:
                        logger.info(u'即将进入全局等待时间，%d秒后程序继续执行' %
                                    self.global_wait[0][1])
                        for i in tqdm(range(self.global_wait[0][1])):
                            sleep(1)
                        self.page_count = 0
                        self.global_wait.append(self.global_wait.pop(0))

                # 更新用户user_id_list.txt中的since_date
                if self.user_config_file_path or FLAGS.u:
                    config_util.update_user_config_file(
                        self.user_config_file_path,
                        self.user_config['user_uri'],
                        self.user.nickname,
                        self.new_since_date,
                    )
        except Exception as e:
            logger.exception(e)

    def _get_filepath(self, type):
        """获取结果文件路径"""
        try:
            dir_name = self.user.nickname
            if self.result_dir_name:
                dir_name = self.user.id
            if FLAGS.output_dir is not None:
                file_dir = FLAGS.output_dir + os.sep + dir_name
            else:
                file_dir = (os.getcwd() + os.sep + 'weibo' + os.sep + dir_name)
            if type == 'img' or type == 'video':
                file_dir = file_dir + os.sep + type
            if not os.path.isdir(file_dir):
                os.makedirs(file_dir)
            if type == 'img' or type == 'video':
                return file_dir
            file_path = file_dir + os.sep + self.user.id + '.' + type
            return file_path
        except Exception as e:
            logger.exception(e)

    def initialize_info(self, user_config):
        """初始化爬虫信息"""
        self.got_num = 0
        self.user_config = user_config
        self.weibo_id_list = []
        if self.end_date == 'now':
            self.new_since_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        else:
            self.new_since_date = self.end_date
        self.writers = []
        if 'csv' in self.write_mode:
            from weiboSpider.weibo_spider.writer import CsvWriter

            self.writers.append(
                CsvWriter(self._get_filepath('csv'), self.filter))
        if 'txt' in self.write_mode:
            from weiboSpider.weibo_spider.writer import TxtWriter

            self.writers.append(
                TxtWriter(self._get_filepath('txt'), self.filter))
        if 'json' in self.write_mode:
            from weiboSpider.weibo_spider.writer import JsonWriter

            self.writers.append(JsonWriter(self._get_filepath('json')))
        if 'mysql' in self.write_mode:
            from weiboSpider.weibo_spider.writer import MySqlWriter

            self.writers.append(MySqlWriter(self.mysql_config))
        if 'mongo' in self.write_mode:
            from weiboSpider.weibo_spider.writer import MongoWriter

            self.writers.append(MongoWriter(self.mongo_config))
        if 'sqlite' in self.write_mode:
            from weiboSpider.weibo_spider.writer import SqliteWriter

            self.writers.append(SqliteWriter(self.sqlite_config))

        if 'kafka' in self.write_mode:
            from weiboSpider.weibo_spider.writer import KafkaWriter

            self.writers.append(KafkaWriter(self.kafka_config))

        if 'post' in self.write_mode:
            from weiboSpider.weibo_spider.writer import PostWriter

            self.writers.append(PostWriter(self.post_config))

        self.downloaders = []
        if self.pic_download == 1:
            from weiboSpider.weibo_spider.downloader import (OriginPictureDownloader,
                                                             RetweetPictureDownloader)

            self.downloaders.append(
                OriginPictureDownloader(self._get_filepath('img'),
                                        self.file_download_timeout))
        if self.pic_download and not self.filter:
            self.downloaders.append(
                RetweetPictureDownloader(self._get_filepath('img'),
                                         self.file_download_timeout))
        if self.video_download == 1:
            from weiboSpider.weibo_spider.downloader import VideoDownloader

            self.downloaders.append(
                VideoDownloader(self._get_filepath('video'),
                                self.file_download_timeout))

    def get_one_user(self, user_config):
        """获取一个用户的微博"""
        try:
            self.get_user_info(user_config['user_uri'])
            if self.user is None:
                logger.info(f'{user_config["user_uri"]} is not a valid user id')
                return
            logger.info(self.user)
            logger.info('*' * 100)

            self.initialize_info(user_config)
            self.write_user(self.user)
            logger.info('*' * 100)

            # 下载用户头像相册中的图片。
            if self.pic_download:
                self.download_user_avatar(user_config['user_uri'])

            for weibos in self.get_weibo_info():
                self.write_weibo(weibos)
                self.got_num += len(weibos)
            if not self.filter:
                logger.info(u'共爬取' + str(self.got_num) + u'条微博')
            else:
                logger.info(u'共爬取' + str(self.got_num) + u'条原创微博')
            logger.info(u'信息抓取完毕')
            logger.info('*' * 100)
        except Exception as e:
            logger.exception(e)

    def start(self):
        """运行爬虫"""
        try:
            if not self.user_config_list:
                logger.info(
                    u'没有配置有效的user_id，请通过config.json或user_id_list.txt配置user_id')
                return
            user_count = 0
            user_count1 = random.randint(*self.random_wait_pages)
            random_users = random.randint(*self.random_wait_pages)
            for user_config in self.user_config_list:
                if (user_count - user_count1) % random_users == 0:
                    sleep(random.randint(*self.random_wait_seconds))
                    user_count1 = user_count
                    random_users = random.randint(*self.random_wait_pages)
                user_count += 1
                self.get_one_user(user_config)
        except Exception as e:
            logger.exception(e)


def _get_config():
    """获取config.json数据"""
    src = os.path.split(
        os.path.realpath(__file__))[0] + os.sep + 'config_sample.json'
    config_path = os.getcwd() + os.sep + 'config.json'
    if FLAGS.config_path:
        config_path = FLAGS.config_path
    elif not os.path.isfile(config_path):
        shutil.copy(src, config_path)
        logger.info(u'请先配置当前目录(%s)下的config.json文件，'
                    u'如果想了解config.json参数的具体意义及配置方法，请访问\n'
                    u'https://github.com/dataabc/weiboSpider#2程序设置' %
                    os.getcwd())
        sys.exit()
    try:
        with open(config_path) as f:
            try:
                config_util.check_cookie(config_path)
            except Exception:
                logger.info("Using the cookie field in config.json as the request cookie.")
            config = json.loads(f.read())
            return config
    except ValueError:
        logger.error(u'config.json 格式不正确，请访问 '
                     u'https://github.com/dataabc/weiboSpider#2程序设置')
        sys.exit()


def main(_):
    try:
        config = {
            "user_id_list": ["1223178222"],
            "filter": 1,
            "since_date": "2025-03-01",
            "end_date": "now",
            "random_wait_pages": [1, 5],
            "random_wait_seconds": [6, 10],
            "global_wait": [[1000, 3600], [500, 2000]],
            "write_mode": ["csv", "txt", "json"],
            "pic_download": 1,
            "video_download": 0,
            "file_download_timeout": [5, 5, 10],
            "result_dir_name": 1,
            "cookie": "SCF=AkmHhln62YDWFSFl1vzulQ-Wd09yddy7K-VnCJTtefEZwQpHyTQ8rcB-6LO65zIESqUfTmwTKhnxkYr2kee1cLk.; SUB=_2A25K9_PVDeRhGeFH6FYT8ibLwj2IHXVpjQkdrDV6PUJbktANLUPAkW1Ne36qaB-BH-V5wti5RpbFJ5Gb6fAjFDg0; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFRqula4izcRzF_cgpYMsE.5NHD95QN1KeXeozRS0.pWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0.0ShzE1hM4eBtt; SSOLoginState=1744012165; ALF=1746604165",
        }

        config_util.validate_config(config)
        wb = Spider(config)
        wb.start()  # 爬取微博信息
        pass
    except Exception as e:
        logger.exception(e)


def generate_random_10_digit_string():
    # 生成一个10位数字字符串，第一位不为0
    first_digit = str(random.randint(0, 9))
    rest_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    return first_digit + rest_digits


def random_fetch(_):
    count = 0
    current_uid = ''
    while count < 10:
        users = json.loads(open('./uids.json', 'r', encoding='utf-8').read())
        try:
            # random.seed(time.time())
            current_uid = generate_random_10_digit_string()
            # current_uid = '1223178222'
            while current_uid in users['do_not_fetch'] or current_uid in users['null_uids']:
                current_uid = generate_random_10_digit_string()
            current_config = global_config.copy()
            current_config['user_id_list'] = [current_uid]
            config_util.validate_config(current_config)
            wb = Spider(current_config)
            wb.start()  # 爬取微博信息
            if wb.user is not None:
                if len(wb.weibo_id_list) == 0:
                    if users['no_weibo'].get(current_uid) is None:
                        users['no_weibo'][current_uid] = {
                            'id': current_uid,
                            'last_fetch': str(date.today()),
                            'meta': {
                                str(date.today()): wb.user.__dict__
                            },
                            'weibo_id_list': {
                                str(date.today()): wb.weibo_id_list
                            }
                        }
                    else:
                        users['no_weibo'][current_uid]['last_fetch'] = str(date.today())
                        users['no_weibo'][current_uid]['meta'][str(date.today())] = wb.user.__dict__
                        users['no_weibo'][current_uid]['weibo_id_list'][str(date.today())] = wb.weibo_id_list
                else:
                    count += 1
                    if users['fetched'].get(current_uid) is None:
                        users['fetched'][current_uid] = {
                            'id': current_uid,
                            'last_fetch': str(date.today()),
                            'meta': {
                                str(date.today()): wb.user.__dict__
                            },
                            'weibo_id_list': {
                                str(date.today()): wb.weibo_id_list
                            }
                        }
                    else:
                        users['fetched'][current_uid]['last_fetch'] = str(date.today())
                        users['fetched'][current_uid]['meta'][str(date.today())] = wb.user.__dict__
                        users['fetched'][current_uid]['weibo_id_list'][str(date.today())] = wb.weibo_id_list
            else:
                users['null_uids'].append(current_uid)
            pass
        except Exception as e:
            logger.exception(e)

        with open('./uids.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(users, ensure_ascii=False))
        sleep(60 + random.randint(0, 60))


if __name__ == '__main__':
    # app.run(main)
    app.run(random_fetch)
