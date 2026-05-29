# -*-coding:utf8-*-

import datetime
import json
import os
import random
import sys
import time

import pymysql
import requests
from multiprocessing.dummy import Pool as ThreadPool

try:
    from importlib import reload
except ImportError:
    from imp import reload

from user_profile import user_profile_decorator, save_user_profile

reload(sys)

REQUEST_TIMEOUT = 10
REQUEST_RETRIES = 3
REQUEST_INTERVAL_RANGE = (0.8, 1.8)
COOKIE = os.environ.get('BILIBILI_COOKIE', '').strip()
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'passwd': '123456',
    'db': 'bilibili',
    'charset': 'utf8'
}
DEFAULT_HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://space.bilibili.com/45388',
    'Origin': 'https://space.bilibili.com',
    'Host': 'api.bilibili.com',
    'AlexaToolbar-ALX_NS_PH': 'AlexaToolbar/alx-4.0',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
    'Accept': 'application/json, text/javascript, */*; q=0.01'
}
INSERT_SQL = '''
INSERT INTO bilibili_user_info(
    mid, name, sex, rank, face, regtime, spacesta, birthday, sign, level,
    OfficialVerifyType, OfficialVerifyDesc, vipType, vipStatus, toutu, toutuId,
    coins, following, fans, archiveview, article
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
'''


def datetime_to_timestamp_in_milliseconds(d):
    return int(round(time.time() * 1000))


def load_user_agents(uafile):
    uas = []
    with open(uafile, 'r') as uaf:
        for ua in uaf.readlines():
            ua = ua.strip()
            if ua:
                uas.append(ua)
    random.shuffle(uas)
    return uas


uas = load_user_agents('user_agents.txt')
session = requests.Session()
if COOKIE:
    session.headers.update({'Cookie': COOKIE})

time1 = time.time()
urls = []

for m in range(5214, 5215):
    for i in range(m * 100, (m + 1) * 100):
        urls.append('https://space.bilibili.com/' + str(i))


def build_headers(mid):
    headers = dict(DEFAULT_HEADERS)
    headers['User-Agent'] = random.choice(uas)
    headers['Referer'] = 'https://space.bilibili.com/%s?from=search&seid=%s' % (mid, random.randint(10000, 50000))
    return headers


def request_json(url, headers=None, params=None):
    for attempt in range(REQUEST_RETRIES):
        try:
            response = session.get(
                url,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(e)
        if attempt < REQUEST_RETRIES - 1:
            time.sleep(random.uniform(0.5, 1.5))
    return None


@user_profile_decorator
def fetch_user_data(url):
    mid = url.replace('https://space.bilibili.com/', '')
    payload = {
        '_': datetime_to_timestamp_in_milliseconds(datetime.datetime.now()),
        'mid': mid
    }
    headers = build_headers(mid)

    js_dict = request_json(
        'https://api.bilibili.com/x/space/acc/info',
        headers=headers,
        params=payload
    )
    if not js_dict:
        return None

    status_code = js_dict['code'] if 'code' in js_dict.keys() else False
    if status_code != 0 or 'data' not in js_dict.keys():
        return None

    js_data = js_dict['data'] or {}
    official_data = js_data.get('official') or {}
    vip_data = js_data.get('vip') or {}
    regtimestamp = js_data.get('jointime') or 0
    regtime = ''
    if regtimestamp:
        regtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(regtimestamp))

    user_data = {
        'mid': js_data.get('mid', mid),
        'name': js_data.get('name', ''),
        'sex': js_data.get('sex', '保密'),
        'rank': js_data.get('rank', 0),
        'face': js_data.get('face', ''),
        'regtimestamp': regtimestamp,
        'regtime': regtime,
        'spacesta': '',
        'birthday': js_data['birthday'] if 'birthday' in js_data.keys() else 'nobirthday',
        'sign': js_data.get('sign', ''),
        'level': js_data.get('level', 0),
        'OfficialVerifyType': official_data.get('type', 0),
        'OfficialVerifyDesc': official_data.get('desc', ''),
        'vipType': vip_data.get('type', 0),
        'vipStatus': vip_data.get('status', 0),
        'toutu': '',
        'toutuId': 0,
        'coins': js_data.get('coins', 0),
        'following': 0,
        'fans': 0,
        'archiveview': 0,
        'article': 0
    }

    relation_data = request_json(
        'https://api.bilibili.com/x/relation/stat',
        headers=headers,
        params={'vmid': mid, 'jsonp': 'jsonp'}
    )
    if relation_data and relation_data.get('data'):
        relation = relation_data.get('data') or {}
        user_data['following'] = relation.get('following', 0)
        user_data['fans'] = relation.get('follower', 0)

    return user_data


def save_user_data(user_data):
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            INSERT_SQL,
            (
                user_data.get('mid', 0),
                user_data.get('name', ''),
                user_data.get('sex', '保密'),
                user_data.get('rank', 0),
                user_data.get('face', ''),
                user_data.get('regtime', ''),
                user_data.get('spacesta', ''),
                user_data.get('birthday', 'nobirthday'),
                user_data.get('sign', ''),
                user_data.get('level', 0),
                user_data.get('OfficialVerifyType', 0),
                user_data.get('OfficialVerifyDesc', ''),
                user_data.get('vipType', 0),
                user_data.get('vipStatus', 0),
                user_data.get('toutu', ''),
                user_data.get('toutuId', 0),
                user_data.get('coins', 0),
                user_data.get('following', 0),
                user_data.get('fans', 0),
                user_data.get('archiveview', 0),
                user_data.get('article', 0)
            )
        )
        conn.commit()

        if 'tags' in user_data and 'churn_prediction' in user_data:
            save_user_profile(conn, user_data)
            print('User profile saved for mid: ' + str(user_data.get('mid')))
    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()


def getsource(url):
    time.sleep(random.uniform(*REQUEST_INTERVAL_RANGE))
    time2 = time.time()
    user_data = fetch_user_data(url)

    if not user_data:
        print('Error: ' + url)
        return None

    print('Succeed get user info: ' + str(user_data['mid']) + '\t' + str(time2 - time1))
    save_user_data(user_data)
    return user_data


if __name__ == '__main__':
    pool = ThreadPool(1)
    try:
        results = pool.map(getsource, urls)
    except Exception as e:
        print(e)

    pool.close()
    pool.join()
