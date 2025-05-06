import asyncio
import json
import os
from time import sleep, time
from random import randint
from twikit.guest import GuestClient
from datetime import datetime
from curd_mysql import select_from_table, insert_into_table_transformation, insert_into_table, update_table

MEDIA_TYPE = {
    'photo': '0',
    'video': '1',
    'animated_gif': '2'
}


def get_tweet_id_list_from_database(start=None, end=None):
    cnf = json.load(open('./connect_db.json', 'r', encoding='utf-8'))
    if start is not None and end is not None:
        start -= 1
        end += 1
        data = select_from_table(cnf, 'tweet_id', condition=f'{start} < id AND id < {end} AND fetched_flag = 0')
    else:
        data = select_from_table(cnf, 'tweet_id')
    return data


async def main():
    client = GuestClient(proxy="http://127.0.0.1:30000")
    # Activate the client by generating a guest token.
    await client.activate()
    sleep(10 + randint(1, 10))

    cnf = json.load(open('./connect_db.json', 'r', encoding='utf-8'))
    all_users = set()
    for item in select_from_table(cnf, 'tweet_user', columns=['id']):
        all_users.add(item['id'])

    start_time = time()
    limit_time = (10 + randint(0, 5)) * 60  # 每过一段时间停一次

    client_count = 1
    count = 1
    run_times = randint(25, 35)
    start = time()

    for tid in get_tweet_id_list_from_database(start=504, end=1000):
        if randint(0, 1):
            sleep(randint(5, 15))

        if client_count % 100 == 0:
            print('Reset client')
            client = GuestClient(proxy="http://127.0.0.1:30000")
            # Activate the client by generating a guest token.
            await client.activate()
            sleep(10)

        if time() - start_time > limit_time or count % run_times == 0:
            temp = randint(300, 1000)
            print(f'Waiting {temp} seconds')
            sleep(temp)
            limit_time = (10 + randint(0, 5)) * 60
            run_times = randint(25, 35)
            start_time = time()

        tweet_id = tid['tweet_id']
        tweet = await client.get_tweet_by_id(tweet_id)
        if tweet is None:
            print(f'Tweet {tweet_id} not found')
            continue

        meta_info = {
            "id": tweet.user.id,
            "add_date": datetime.now(),
            "name": tweet.user.name,
            "created_at": datetime.strptime(tweet.user.created_at, '%a %b %d %H:%M:%S %z %Y'),
            "followers_count": tweet.user.followers_count,
            "following_count": tweet.user.following_count,
            "favourites_count": tweet.user.favourites_count,
            "screen_name": tweet.user.screen_name,
            "description": tweet.user.description,
            "location": tweet.user.location,
        }

        # 写入用户信息表
        if meta_info['id'] not in all_users:
            print(f'用户\t{meta_info["name"]}\t{meta_info["id"]}存入表')
            insert_into_table_transformation(cnf, 'tweet_user', meta_info)
        else:
            print(f'用户\t{meta_info["name"]}\t{meta_info["id"]}已在表中')

        data = {
            "tweet_id": tweet.id,
            "add_date": datetime.now(),
            "user_id": tweet.user.id,
            "in_reply_to": tweet.in_reply_to,
            "created_at": datetime.strptime(tweet.created_at, '%a %b %d %H:%M:%S %z %Y'),
            "text": tweet.text,
            "full_text": tweet.full_text,
            "lang": tweet.lang,
            "possibly_sensitive": tweet.possibly_sensitive,
            "possibly_sensitive_editable": tweet.possibly_sensitive_editable,
            "has_media": False,
            "reply_count": tweet.reply_count,
            "favorite_count": tweet.favorite_count,
            "favorited": tweet.favorited,
            "retweet_count": tweet.retweet_count,
            "bookmark_count": tweet.bookmark_count,
            "bookmarked": tweet.bookmarked,
            "editable_until_msecs": tweet.editable_until_msecs,
            "is_translatable": tweet.is_translatable,
            "is_edit_eligible": tweet.is_edit_eligible,
            "edits_remaining": tweet.edits_remaining,
            "view_count": tweet.view_count,
            "view_count_state": tweet.view_count_state,
            "is_quote_status": tweet.is_quote_status,
            "quote_count": tweet.quote_count,
            "quote": None,
            # "retweeted_tweet": tweet.retweeted_tweet,
            # "urls": tweet.urls,
            "hashtags": json.dumps(tweet.hashtags),
            # "has_community_notes": tweet.has_community_notes,
            # "community_note": tweet.community_note,
            "has_card": tweet.has_card,
        }

        # 创建存储文件夹 写入推文文本
        if not os.path.exists(f'tweet/{tweet.user.id}'):
            os.mkdir(f'tweet/{tweet.user.id}')
            print(f'创建用户文件夹\t{tweet.user.id}\t成功')
        if not os.path.exists(f'tweet/{tweet.user.id}/{tweet.id}'):
            os.mkdir(f'tweet/{tweet.user.id}/{tweet.id}')
        with open(f'tweet/{tweet.user.id}/{tweet.id}/full_text.txt', 'w', encoding='utf-8') as f:
            f.write(tweet.full_text)
        print(f'存储推文\t{tweet.user.id}/{tweet.id}成功')

        if tweet.is_quote_status:
            print(f'当前推特\t{tweet_id}\t为quote\n指向推特\t{tweet.quote.id}')
            print(f'追加推特id\t{tweet.quote.id}')
            insert_into_table(cnf, 'tweet_id', {
                'tweet_id': tweet.quote.id,
                'add_date': 'NOW()',
            })
            data['quote'] = tweet.quote.id

        try:
            if isinstance(tweet.media, list) and len(tweet.media) > 0:
                data['has_media'] = True
                if not os.path.exists(f'tweet/{tweet.user.id}/{tweet.id}/img'):
                    os.mkdir(f'tweet/{tweet.user.id}/{tweet.id}/img')
                for media in tweet.media:
                    media_data = {
                        "id": media.id,
                        "media_type": MEDIA_TYPE[media.type],
                        "media_url": media.media_url,
                        "url": media.url,
                        "tweet_id": tweet_id
                    }
                    print(f'开始下载 {media.type}\t{tweet.user.id}\t{tweet.id}\t{media.id}')
                    download_sep = randint(0, 1) + 1
                    sleep(download_sep)
                    try:
                        await media.download(f'tweet/{tweet.user.id}/{tweet.id}/img/{media.id}.jpg')
                        print(f'下载成功 保存至 tweet/{tweet.user.id}/{tweet.id}/img/{media.id}.jpg')
                    except Exception as e:
                        print('下载失败')
                        print(e)
                    try:
                        insert_into_table_transformation(cnf, 'tweet_media', media_data)
                        print(f'推文{tweet.user.id}/{tweet.id}/{media.id}媒体写入数据库成功')
                    except Exception as e:
                        print(f'推文{tweet.user.id}/{tweet.id}/{media.id}媒体写入失败')
                        print(e)
                    # Only restore jpgs
                    # if media.type == 'photo':
                    #
                    #     pass
                    #
                    # elif media.type == 'video':
                    #
                    #     pass
                    # elif media.type == 'animated_gif':
                    #
                    #     pass
        except:
            print(f'Current tweet {tweet_id} has no media')

        try:
            insert_into_table_transformation(cnf, 'tweet', data)
            print(f'推文{tweet.user.id}/{tweet.id}写入数据库成功')
            update_table(cnf, 'tweet_id', {'fetched_flag': 1}, {'tweet_id': tweet_id})
            print(f'更新{tweet.id}状态成功')
        except Exception as e:
            print(f'推文{tweet.user.id}/{tweet.id}写入失败')
            print(e)

        # 每条推文间隔时间
        sep = randint(5, 15)
        print(f'间隔 {sep} seconds')
        count += 1
        client_count += 1
        print(f'{"="*20}\nUse time {time() - start} seconds\nAverage time {(time() - start) / count} seconds\n{"="*20}')
        sleep(sep)


if __name__ == '__main__':
    asyncio.run(main())
