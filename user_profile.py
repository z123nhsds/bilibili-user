
# -*-coding:utf8-*-

import pymysql
import numpy as np
from datetime import datetime, timedelta
import json
from collections import defaultdict


def connect_db(host='localhost', user='root', passwd='123456', db='bilibili'):
    return pymysql.connect(
        host=host, user=user, passwd=passwd, db=db, charset='utf8'
    )


def generate_user_tags(user_data):
    tags = []
    
    mid = user_data.get('mid')
    name = user_data.get('name', '')
    sex = user_data.get('sex', '保密')
    level = int(user_data.get('level', 0))
    coins = int(user_data.get('coins', 0))
    fans = int(user_data.get('fans', 0))
    following = int(user_data.get('following', 0))
    birthday = user_data.get('birthday', 'nobirthday')
    sign = user_data.get('sign', '')
    regtime = user_data.get('regtime', '')
    OfficialVerifyType = int(user_data.get('OfficialVerifyType', 0))
    vipType = int(user_data.get('vipType', 0))
    vipStatus = int(user_data.get('vipStatus', 0))
    
    if sex == '男':
        tags.append('男性用户')
    elif sex == '女':
        tags.append('女性用户')
    else:
        tags.append('性别保密')
    
    if level == 0:
        tags.append('未激活用户')
    elif level == 1 or level == 2:
        tags.append('非活跃用户')
    elif level == 3 or level == 4:
        tags.append('活跃用户')
    elif level == 5 or level == 6:
        tags.append('核心用户')
    
    if level &gt;= 3:
        tags.append('资深用户')
    
    if fans &gt; 1000000:
        tags.append('超级大V')
    elif fans &gt; 100000:
        tags.append('大V用户')
    elif fans &gt; 10000:
        tags.append('小V用户')
    elif fans &gt; 1000:
        tags.append('千粉用户')
    elif fans &gt; 100:
        tags.append('百粉用户')
    else:
        tags.append('新用户')
    
    if following &gt; 500:
        tags.append('重度关注者')
    elif following &gt; 100:
        tags.append('中度关注者')
    else:
        tags.append('轻度关注者')
    
    if coins &gt; 10000:
        tags.append('硬币大户')
    elif coins &gt; 1000:
        tags.append('硬币充足')
    else:
        tags.append('硬币紧张')
    
    if birthday != 'nobirthday' and birthday:
        try:
            birth_year = int(birthday.split('-')[0])
            age = datetime.now().year - birth_year
            if age &lt; 18:
                tags.append('未成年')
            elif age &lt; 25:
                tags.append('Z世代')
            elif age &lt; 35:
                tags.append('青年用户')
            elif age &lt; 50:
                tags.append('中年用户')
            else:
                tags.append('资深用户')
        except:
            pass
    
    if OfficialVerifyType &gt; 0:
        tags.append('认证用户')
    
    if vipStatus == 1:
        tags.append('大会员')
        if vipType == 1:
            tags.append('月度大会员')
        elif vipType == 2:
            tags.append('年度大会员')
    
    if regtime:
        try:
            reg_date = datetime.strptime(regtime.split(' ')[0], '%Y-%m-%d')
            days_since_reg = (datetime.now() - reg_date).days
            if days_since_reg &gt; 365 * 5:
                tags.append('五年老用户')
            elif days_since_reg &gt; 365 * 3:
                tags.append('三年老用户')
            elif days_since_reg &gt; 365:
                tags.append('一年老用户')
            else:
                tags.append('新注册用户')
        except:
            pass
    
    if len(sign) &gt; 50:
        tags.append('个性签名达人')
    
    if fans &gt; following * 10:
        tags.append('网络红人')
    
    if following &gt; fans * 10:
        tags.append('社交达人')
    
    if level &gt;= 5 and fans &gt; 10000:
        tags.append('优质UP主')
    
    if len(tags) &lt; 20:
        additional_tags = ['B站会员', '视频爱好者', '二次元用户', '弹幕爱好者', 
                          '社区参与者', '内容消费者', '潜水用户', '评论达人',
                          '点赞狂魔', '收藏爱好者', '分享达人', '打卡用户',
                          '夜猫子', '早起鸟', '周末活跃', '工作日活跃']
        for tag in additional_tags:
            if tag not in tags and len(tags) &lt; 20:
                tags.append(tag)
    
    return tags[:20]


def calculate_churn_probability(user_data, history_data=None):
    level = int(user_data.get('level', 0))
    coins = int(user_data.get('coins', 0))
    fans = int(user_data.get('fans', 0))
    following = int(user_data.get('following', 0))
    regtime = user_data.get('regtime', '')
    
    days_since_reg = 365
    if regtime:
        try:
            reg_date = datetime.strptime(regtime.split(' ')[0], '%Y-%m-%d')
            days_since_reg = (datetime.now() - reg_date).days
        except:
            pass
    
    activity_score = 0
    
    activity_score += level * 10
    
    if coins &gt; 1000:
        activity_score += 20
    elif coins &gt; 100:
        activity_score += 10
    
    if fans &gt; 1000:
        activity_score += 15
    
    if following &gt; 50:
        activity_score += 10
    
    if days_since_reg &lt; 30:
        activity_score += 20
    elif days_since_reg &lt; 180:
        activity_score += 10
    
    activity_score = min(activity_score, 100)
    
    decay_factor = 1.0
    if days_since_reg &gt; 365:
        decay_factor = 0.8
    if days_since_reg &gt; 365 * 3:
        decay_factor = 0.6
    
    activity_score *= decay_factor
    
    churn_probability = 1.0 - (activity_score / 100.0)
    churn_probability = max(0.0, min(1.0, churn_probability))
    
    return {
        'churn_probability_30d': round(churn_probability, 4),
        'activity_score': round(activity_score, 2),
        'decay_factor': round(decay_factor, 2),
        'days_since_registration': days_since_reg
    }


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1, dtype=np.float64)
    vec2 = np.array(vec2, dtype=np.float64)
    
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return np.dot(vec1, vec2) / (norm1 * norm2)


def get_region_vector(region):
    regions = ['北京', '上海', '广东', '江苏', '浙江', '山东', '河南', '四川', 
               '湖北', '湖南', '福建', '陕西', '重庆', '辽宁', '河北', '其他']
    region_lower = region.lower() if region else ''
    
    vector = [0.0] * len(regions)
    for i, r in enumerate(regions):
        if r in region_lower:
            vector[i] = 1.0
            break
    else:
        vector[-1] = 1.0
    
    return vector


def calculate_user_similarity(user1, user2):
    fans1 = int(user1.get('fans', 0))
    level1 = int(user1.get('level', 0))
    region1 = user1.get('spacesta', '')
    
    fans2 = int(user2.get('fans', 0))
    level2 = int(user2.get('level', 0))
    region2 = user2.get('spacesta', '')
    
    max_fans = 1000000
    norm_fans1 = min(fans1 / max_fans, 1.0)
    norm_fans2 = min(fans2 / max_fans, 1.0)
    
    norm_level1 = level1 / 6.0
    norm_level2 = level2 / 6.0
    
    region_vec1 = get_region_vector(region1)
    region_vec2 = get_region_vector(region2)
    
    vec1 = [norm_fans1, norm_level1] + region_vec1
    vec2 = [norm_fans2, norm_level2] + region_vec2
    
    return cosine_similarity(vec1, vec2)


def find_similar_users(target_user, all_users, top_n=10):
    similarities = []
    
    for user in all_users:
        if user['mid'] == target_user['mid']:
            continue
        sim = calculate_user_similarity(target_user, user)
        similarities.append((user, sim))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:top_n]


def user_profile_decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        if result and isinstance(result, dict) and 'mid' in result:
            user_data = result
            
            tags = generate_user_tags(user_data)
            churn_prediction = calculate_churn_probability(user_data)
            
            user_data['tags'] = tags
            user_data['churn_prediction'] = churn_prediction
        
        return result
    return wrapper


def save_user_profile(conn, user_data):
    try:
        cur = conn.cursor()
        
        tags_json = json.dumps(user_data.get('tags', []), ensure_ascii=False)
        churn_pred = user_data.get('churn_prediction', {})
        
        cur.execute('''
            INSERT INTO bilibili_user_profile 
            (mid, tags, churn_probability_30d, activity_score, decay_factor, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
            tags = VALUES(tags),
            churn_probability_30d = VALUES(churn_probability_30d),
            activity_score = VALUES(activity_score),
            decay_factor = VALUES(decay_factor),
            updated_at = NOW()
        ''', (
            user_data['mid'],
            tags_json,
            churn_pred.get('churn_probability_30d', 0),
            churn_pred.get('activity_score', 0),
            churn_pred.get('decay_factor', 1.0)
        ))
        
        conn.commit()
    except Exception as e:
        print(f"Error saving user profile: {e}")


def get_user_profile(conn, mid):
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM bilibili_user_profile WHERE mid = %s', (mid,))
        result = cur.fetchone()
        
        if result:
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, result))
    except Exception as e:
        print(f"Error getting user profile: {e}")
    
    return None


def batch_generate_profiles(conn, limit=1000):
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM bilibili_user_info LIMIT %s', (limit,))
        users = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        
        for user_row in users:
            user_data = dict(zip(columns, user_row))
            tags = generate_user_tags(user_data)
            churn_prediction = calculate_churn_probability(user_data)
            
            user_data['tags'] = tags
            user_data['churn_prediction'] = churn_prediction
            
            save_user_profile(conn, user_data)
        
        print(f"Generated profiles for {len(users)} users")
    except Exception as e:
        print(f"Error in batch generation: {e}")

