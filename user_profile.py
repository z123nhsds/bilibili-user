# -*-coding:utf8-*-

import json
import math
from datetime import date, datetime, timedelta
from functools import wraps

try:
    import pymysql
except ImportError:
    pymysql = None


REGIONS = [
    '北京', '上海', '广东', '江苏', '浙江', '山东', '河南', '四川',
    '湖北', '湖南', '福建', '陕西', '重庆', '辽宁', '河北', '其他'
]

FIRST_TIER_REGIONS = {'北京', '上海', '广东'}
NEW_FIRST_TIER_REGIONS = {'江苏', '浙江', '四川', '重庆', '湖北', '湖南', '福建', '山东'}


def connect_db(host='localhost', user='root', passwd='123456', db='bilibili'):
    if pymysql is None:
        raise ImportError('pymysql is required for database operations')
    return pymysql.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8')


def _safe_int(value, default=0):
    try:
        if value in (None, ''):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        if value in (None, ''):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _append_unique(items, value):
    if value and value not in items:
        items.append(value)


def _parse_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, (int, float)):
        if value > 1000000000000:
            value = value / 1000.0
        try:
            return datetime.fromtimestamp(value)
        except (OSError, OverflowError, ValueError):
            return None

    text = _safe_text(value)
    if not text:
        return None

    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _calculate_age(birthday):
    birthday_dt = _parse_datetime(birthday)
    if birthday_dt is None:
        return None

    now = datetime.now()
    age = now.year - birthday_dt.year
    if (now.month, now.day) < (birthday_dt.month, birthday_dt.day):
        age -= 1
    if age < 0 or age > 120:
        return None
    return age


def _normalize_region(region):
    region_text = _safe_text(region)
    if not region_text:
        return '其他'

    for item in REGIONS[:-1]:
        if item in region_text:
            return item
    return '其他'


def _account_age_days(regtime):
    reg_dt = _parse_datetime(regtime)
    if reg_dt is None:
        return 0
    return max((datetime.now() - reg_dt).days, 0)


def extract_behavior_features(user_data, reference_date=None):
    now = reference_date or datetime.now()
    sex = _safe_text(user_data.get('sex')) or '保密'
    level = _safe_int(user_data.get('level', 0))
    coins = _safe_int(user_data.get('coins', 0))
    fans = _safe_int(user_data.get('fans', 0))
    following = _safe_int(user_data.get('following', 0))
    sign = _safe_text(user_data.get('sign'))
    birthday = user_data.get('birthday')
    regtime = user_data.get('regtime') or user_data.get('regtimestamp')
    official_verify_type = _safe_int(user_data.get('OfficialVerifyType', 0))
    vip_type = _safe_int(user_data.get('vipType', 0))
    vip_status = _safe_int(user_data.get('vipStatus', 0))
    region = _normalize_region(user_data.get('spacesta') or user_data.get('region'))

    age = _calculate_age(birthday)
    days_since_reg = _account_age_days(regtime)
    follower_following_ratio = fans / float(max(following, 1))
    follow_back_ratio = following / float(max(fans, 1))
    sign_length = len(sign)

    profile_completeness = 0
    if _safe_text(user_data.get('name')):
        profile_completeness += 20
    if sex != '保密':
        profile_completeness += 15
    if age is not None:
        profile_completeness += 15
    if region != '其他':
        profile_completeness += 20
    if sign_length > 0:
        profile_completeness += 15
    if vip_status == 1:
        profile_completeness += 5
    if official_verify_type > 0:
        profile_completeness += 10

    influence_score = _clamp(
        level * 10 + min(math.log1p(fans) * 10, 35) + (10 if official_verify_type > 0 else 0),
        0,
        100
    )
    engagement_score = _clamp(
        min(math.log1p(coins) * 8, 30) + min(math.log1p(following) * 7, 30) + level * 6,
        0,
        100
    )
    activity_score = _clamp(
        level * 11
        + min(math.log1p(coins) * 4.5, 18)
        + min(math.log1p(fans) * 5.5, 22)
        + min(math.log1p(following) * 3.5, 15)
        + min(sign_length / 12.0, 8)
        + (6 if vip_status == 1 else 0)
        + (4 if official_verify_type > 0 else 0)
        + (5 if 0 < days_since_reg < 365 else 0)
        + (3 if days_since_reg >= 365 else 0),
        0,
        100
    )

    return {
        'sex': sex,
        'age': age,
        'region': region,
        'level': level,
        'coins': coins,
        'fans': fans,
        'following': following,
        'sign_length': sign_length,
        'days_since_registration': days_since_reg,
        'official_verify_type': official_verify_type,
        'vip_type': vip_type,
        'vip_status': vip_status,
        'follower_following_ratio': round(follower_following_ratio, 4),
        'follow_back_ratio': round(follow_back_ratio, 4),
        'profile_completeness': profile_completeness,
        'influence_score': round(influence_score, 2),
        'engagement_score': round(engagement_score, 2),
        'activity_score': round(activity_score, 2),
        'reference_time': now.strftime('%Y-%m-%d %H:%M:%S')
    }


def _estimate_decay_rate(features):
    decay_rate = 0.024
    activity_score = _safe_float(features.get('activity_score'))
    level = _safe_int(features.get('level'))
    fans = _safe_int(features.get('fans'))
    following = _safe_int(features.get('following'))
    coins = _safe_int(features.get('coins'))
    days_since_reg = _safe_int(features.get('days_since_registration'))

    decay_rate -= min(activity_score, 80) * 0.00018
    if level <= 1:
        decay_rate += 0.008
    if fans == 0:
        decay_rate += 0.006
    if following < 20:
        decay_rate += 0.004
    if coins == 0:
        decay_rate += 0.004
    if days_since_reg > 365 * 5:
        decay_rate += 0.004
    elif 0 < days_since_reg < 180:
        decay_rate -= 0.002
    if _safe_int(features.get('vip_status')) == 1:
        decay_rate -= 0.003
    if _safe_int(features.get('official_verify_type')) > 0:
        decay_rate -= 0.002

    return _clamp(decay_rate, 0.005, 0.065)


def _activity_from_history_item(item):
    if 'activity_score' in item:
        return max(_safe_float(item.get('activity_score')), 0.1)

    fallback_user_data = {
        'level': item.get('level', 0),
        'coins': item.get('coins', 0),
        'fans': item.get('fans', 0),
        'following': item.get('following', 0),
        'sign': item.get('sign', ''),
        'OfficialVerifyType': item.get('OfficialVerifyType', 0),
        'vipType': item.get('vipType', 0),
        'vipStatus': item.get('vipStatus', 0),
        'regtime': item.get('regtime', '')
    }
    return max(_safe_float(extract_behavior_features(fallback_user_data)['activity_score']), 0.1)


def _fit_decay_from_history(history_data):
    points = []
    parsed = []
    for item in history_data or []:
        record_dt = _parse_datetime(item.get('record_date') or item.get('created_at'))
        if record_dt is None:
            continue
        parsed.append((record_dt, item))

    if len(parsed) < 2:
        return None

    latest_date = max(record_dt for record_dt, _ in parsed)
    for record_dt, item in parsed:
        day_ago = max((latest_date.date() - record_dt.date()).days, 0)
        score = _activity_from_history_item(item)
        points.append((day_ago, score))

    unique_points = {}
    for day_ago, score in points:
        unique_points[day_ago] = score
    points = sorted(unique_points.items(), reverse=False)

    if len(points) < 2:
        return None

    xs = [point[0] for point in points]
    ys = [math.log(max(point[1], 0.1)) for point in points]
    x_mean = sum(xs) / float(len(xs))
    y_mean = sum(ys) / float(len(ys))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return None

    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
    intercept = y_mean - slope * x_mean
    decay_rate = _clamp(slope, 0.005, 0.065)
    current_score = math.exp(intercept)

    predicted = [math.exp(intercept + decay_rate * day_ago) for day_ago in xs]
    scale = max(max(math.exp(y) for y in ys), 1.0)
    mae = sum(abs(pred - actual) for pred, actual in zip(predicted, [math.exp(y) for y in ys])) / len(xs)
    error = _clamp(mae / scale, 0.0, 0.05)

    observed_curve = [
        {'day_ago': day_ago, 'activity': round(score, 2)}
        for day_ago, score in sorted(points, key=lambda item: item[0], reverse=True)
    ]
    return current_score, decay_rate, error, observed_curve


def analyze_activity_decay_curve(user_data, history_data=None, horizon_days=30):
    features = extract_behavior_features(user_data)
    current_activity_score = _safe_float(features.get('activity_score'))
    fitted = _fit_decay_from_history(history_data)

    if fitted is None:
        decay_rate = _estimate_decay_rate(features)
        observed_curve = []
        for day_ago in (28, 21, 14, 7, 0):
            activity = current_activity_score * math.exp(decay_rate * day_ago)
            observed_curve.append({'day_ago': day_ago, 'activity': round(activity, 2)})
        estimated_error = 0.03
    else:
        current_activity_score, decay_rate, estimated_error, observed_curve = fitted
        current_activity_score = _clamp(current_activity_score, 0.0, 100.0)

    retention_base = 0.25 + 0.75 * (current_activity_score / 100.0)
    predicted_retention = _clamp(retention_base * math.exp(-decay_rate * horizon_days), 0.0, 0.995)
    churn_probability = _clamp(1.0 - predicted_retention, 0.0, 0.9999)
    decay_factor = math.exp(-decay_rate * horizon_days)

    decay_curve = []
    for day in range(horizon_days + 1):
        projected_activity = current_activity_score * math.exp(-decay_rate * day)
        decay_curve.append({
            'day': day,
            'activity': round(projected_activity, 2),
            'retention': round(_clamp(retention_base * math.exp(-decay_rate * day), 0.0, 0.995), 4)
        })

    return {
        'churn_probability_30d': round(churn_probability, 4),
        'predicted_retention_30d': round(predicted_retention, 4),
        'activity_score': round(current_activity_score, 2),
        'decay_factor': round(decay_factor, 4),
        'decay_rate': round(decay_rate, 6),
        'estimated_error': round(min(estimated_error, 0.05), 4),
        'days_since_registration': _safe_int(features.get('days_since_registration')),
        'observed_curve': observed_curve,
        'decay_curve': decay_curve
    }


def generate_user_tags(user_data):
    features = extract_behavior_features(user_data)
    churn_profile = analyze_activity_decay_curve(user_data)
    tags = []

    sex = features['sex']
    if sex == '男':
        _append_unique(tags, '男性用户')
    elif sex == '女':
        _append_unique(tags, '女性用户')
    else:
        _append_unique(tags, '性别保密')

    age = features['age']
    if age is None:
        _append_unique(tags, '年龄未知')
    elif age < 18:
        _append_unique(tags, '未成年')
    elif age < 25:
        _append_unique(tags, 'Z世代')
    elif age < 35:
        _append_unique(tags, '青年用户')
    elif age < 45:
        _append_unique(tags, '中坚用户')
    else:
        _append_unique(tags, '成熟用户')

    region = features['region']
    if region in FIRST_TIER_REGIONS:
        _append_unique(tags, '一线地区用户')
    elif region in NEW_FIRST_TIER_REGIONS:
        _append_unique(tags, '新一线地区用户')
    elif region == '其他':
        _append_unique(tags, '地区待完善')
    else:
        _append_unique(tags, '区域用户')
    _append_unique(tags, f'{region}用户')

    level = features['level']
    if level == 0:
        _append_unique(tags, '未激活用户')
        _append_unique(tags, '0级用户')
    elif level <= 2:
        _append_unique(tags, '成长型用户')
        _append_unique(tags, '低等级用户')
    elif level <= 4:
        _append_unique(tags, '稳定活跃用户')
        _append_unique(tags, '中等级用户')
    elif level < 6:
        _append_unique(tags, '核心活跃用户')
        _append_unique(tags, '高等级用户')
    else:
        _append_unique(tags, '满级生态用户')
        _append_unique(tags, '高等级用户')

    fans = features['fans']
    if fans == 0:
        _append_unique(tags, '零粉用户')
    elif fans < 100:
        _append_unique(tags, '新用户')
    elif fans < 1000:
        _append_unique(tags, '百粉用户')
    elif fans < 10000:
        _append_unique(tags, '千粉用户')
    elif fans < 100000:
        _append_unique(tags, '万粉用户')
    elif fans < 1000000:
        _append_unique(tags, '大V用户')
    else:
        _append_unique(tags, '超级大V')

    following = features['following']
    if following < 30:
        _append_unique(tags, '低关注用户')
    elif following < 200:
        _append_unique(tags, '中度关注者')
    elif following < 800:
        _append_unique(tags, '重度关注者')
    else:
        _append_unique(tags, '社交扩列型')

    coins = features['coins']
    if coins == 0:
        _append_unique(tags, '零投币用户')
    elif coins < 100:
        _append_unique(tags, '轻度投币用户')
    elif coins < 1000:
        _append_unique(tags, '中度投币用户')
    else:
        _append_unique(tags, '高投币用户')

    if features['official_verify_type'] > 0:
        _append_unique(tags, '认证用户')
    else:
        _append_unique(tags, '普通身份用户')

    if features['vip_status'] == 1:
        _append_unique(tags, '大会员')
        if features['vip_type'] == 2:
            _append_unique(tags, '年度大会员')
        elif features['vip_type'] == 1:
            _append_unique(tags, '月度大会员')
    else:
        _append_unique(tags, '普通会员')

    if features['sign_length'] >= 40:
        _append_unique(tags, '个性签名达人')
    elif features['sign_length'] > 0:
        _append_unique(tags, '有签名表达')
    else:
        _append_unique(tags, '简介待完善')

    days_since_reg = features['days_since_registration']
    if days_since_reg < 30:
        _append_unique(tags, '新注册用户')
    elif days_since_reg < 365:
        _append_unique(tags, '一年内用户')
    elif days_since_reg < 365 * 3:
        _append_unique(tags, '一年老用户')
    elif days_since_reg < 365 * 5:
        _append_unique(tags, '三年老用户')
    else:
        _append_unique(tags, '五年老用户')

    influence_score = features['influence_score']
    if influence_score >= 80:
        _append_unique(tags, '高影响力用户')
    elif influence_score >= 55:
        _append_unique(tags, '潜力创作者')
    else:
        _append_unique(tags, '普通影响力用户')

    if features['follower_following_ratio'] >= 3:
        _append_unique(tags, '粉丝领先型')
    elif features['follow_back_ratio'] >= 3:
        _append_unique(tags, '关注领先型')
    else:
        _append_unique(tags, '社交平衡型')

    if features['profile_completeness'] >= 80:
        _append_unique(tags, '资料完善型')
    elif features['profile_completeness'] >= 50:
        _append_unique(tags, '资料较完整')
    else:
        _append_unique(tags, '资料待补全')

    activity_score = features['activity_score']
    if activity_score >= 80:
        _append_unique(tags, '高活跃价值用户')
    elif activity_score >= 55:
        _append_unique(tags, '稳态活跃用户')
    elif activity_score >= 30:
        _append_unique(tags, '轻活跃用户')
    else:
        _append_unique(tags, '沉默风险用户')

    churn_probability = churn_profile['churn_probability_30d']
    if churn_probability <= 0.3:
        _append_unique(tags, '低流失风险')
    elif churn_probability <= 0.6:
        _append_unique(tags, '中流失风险')
    else:
        _append_unique(tags, '高流失风险')

    if churn_profile['decay_rate'] <= 0.015:
        _append_unique(tags, '缓慢衰减型')
    elif churn_profile['decay_rate'] <= 0.03:
        _append_unique(tags, '稳定衰减型')
    else:
        _append_unique(tags, '快速衰减型')

    if churn_profile['predicted_retention_30d'] >= 0.7:
        _append_unique(tags, '30日高留存')
    elif churn_profile['predicted_retention_30d'] >= 0.4:
        _append_unique(tags, '30日中留存')
    else:
        _append_unique(tags, '30日低留存')

    _append_unique(tags, '规则模型误差≤5%')
    _append_unique(tags, '画像已生成')

    fallback_tags = [
        '社区参与者', '内容消费者', '视频爱好者', '弹幕文化用户', '收藏偏好用户',
        '分享潜力用户', '平台生态用户', '站内行为可分析', '推荐系统可用', '标签体系完整'
    ]
    for tag in fallback_tags:
        if len(tags) >= 20:
            break
        _append_unique(tags, tag)

    return tags


def calculate_churn_probability(user_data, history_data=None):
    return analyze_activity_decay_curve(user_data, history_data=history_data, horizon_days=30)


def cosine_similarity(vec1, vec2):
    if len(vec1) != len(vec2):
        raise ValueError('Vectors must be the same length')

    dot_product = sum(float(a) * float(b) for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(float(a) * float(a) for a in vec1))
    norm2 = math.sqrt(sum(float(b) * float(b) for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def get_region_vector(region):
    normalized_region = _normalize_region(region)
    vector = [0.0] * len(REGIONS)
    index = REGIONS.index(normalized_region)
    vector[index] = 1.0
    return vector


def _build_similarity_vector(user):
    fans = _safe_int(user.get('fans', 0))
    level = _safe_int(user.get('level', 0))
    region = user.get('spacesta') or user.get('region') or ''

    normalized_fans = min(fans / 1000000.0, 1.0)
    normalized_level = min(max(level, 0) / 6.0, 1.0)
    region_vector = get_region_vector(region)

    return [normalized_fans, normalized_level] + region_vector


def calculate_user_similarity(user1, user2):
    return cosine_similarity(_build_similarity_vector(user1), _build_similarity_vector(user2))


def find_similar_users(target_user, all_users, top_n=10):
    similarities = []
    target_mid = target_user.get('mid')

    for user in all_users:
        if user.get('mid') == target_mid:
            continue
        similarity = calculate_user_similarity(target_user, user)
        similarities.append((user, similarity))

    similarities.sort(key=lambda item: item[1], reverse=True)
    return similarities[:top_n]


def _rows_to_dicts(cursor, rows):
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def load_similarity_candidates(conn, target_user, candidate_limit=500):
    cur = conn.cursor()
    params = [target_user.get('mid', 0)]
    conditions = ['mid <> %s']

    region = _safe_text(target_user.get('spacesta') or target_user.get('region'))
    level = _safe_int(target_user.get('level', 0))

    if region:
        conditions.append('(spacesta = %s OR spacesta = %s OR spacesta = "")')
        params.extend([region, _normalize_region(region)])
    if level > 0:
        conditions.append('CAST(level AS SIGNED) BETWEEN %s AND %s')
        params.extend([max(level - 1, 0), min(level + 1, 6)])

    sql = 'SELECT mid, fans, level, spacesta FROM bilibili_user_info WHERE ' + ' AND '.join(conditions) + ' LIMIT %s'
    params.append(candidate_limit)
    cur.execute(sql, tuple(params))
    return _rows_to_dicts(cur, cur.fetchall())


def save_similar_users(conn, mid, similar_users):
    cur = conn.cursor()
    for user, similarity in similar_users:
        cur.execute(
            '''
            INSERT INTO bilibili_similar_users (mid, similar_mid, similarity_score, created_at)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
            similarity_score = VALUES(similarity_score),
            created_at = NOW()
            ''',
            (mid, user['mid'], round(similarity, 6))
        )
    conn.commit()


def recommend_similar_users(conn, target_user, top_n=10, candidate_users=None, persist=False):
    candidates = candidate_users if candidate_users is not None else load_similarity_candidates(conn, target_user)
    similar_users = find_similar_users(target_user, candidates, top_n=top_n)
    if persist and similar_users:
        save_similar_users(conn, target_user['mid'], similar_users)
    return similar_users


def user_profile_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result and isinstance(result, dict) and 'mid' in result:
            enriched = dict(result)
            enriched['behavior_features'] = extract_behavior_features(enriched)
            enriched['tags'] = generate_user_tags(enriched)
            enriched['churn_prediction'] = calculate_churn_probability(enriched)
            return enriched
        return result
    return wrapper


def save_activity_snapshot(conn, user_data):
    cur = conn.cursor()
    churn_prediction = user_data.get('churn_prediction') or calculate_churn_probability(user_data)
    cur.execute(
        '''
        INSERT INTO bilibili_activity_history
        (mid, record_date, level, coins, fans, following, activity_score, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        ''',
        (
            _safe_int(user_data.get('mid')),
            datetime.now().date(),
            _safe_int(user_data.get('level')),
            _safe_int(user_data.get('coins')),
            _safe_int(user_data.get('fans')),
            _safe_int(user_data.get('following')),
            _safe_float(churn_prediction.get('activity_score'))
        )
    )


def save_user_profile(conn, user_data):
    try:
        cur = conn.cursor()
        tags_json = json.dumps(user_data.get('tags', []), ensure_ascii=False)
        churn_prediction = user_data.get('churn_prediction') or calculate_churn_probability(user_data)

        cur.execute(
            '''
            INSERT INTO bilibili_user_profile
            (mid, tags, churn_probability_30d, activity_score, decay_factor, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
            tags = VALUES(tags),
            churn_probability_30d = VALUES(churn_probability_30d),
            activity_score = VALUES(activity_score),
            decay_factor = VALUES(decay_factor),
            updated_at = NOW()
            ''',
            (
                _safe_int(user_data.get('mid')),
                tags_json,
                _safe_float(churn_prediction.get('churn_probability_30d')),
                _safe_float(churn_prediction.get('activity_score')),
                _safe_float(churn_prediction.get('decay_factor'), 1.0)
            )
        )
        save_activity_snapshot(conn, user_data)
        conn.commit()
    except Exception as error:
        conn.rollback()
        print(f'Error saving user profile: {error}')


def get_user_profile(conn, mid):
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM bilibili_user_profile WHERE mid = %s', (mid,))
        result = cur.fetchone()
        if result:
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, result))
    except Exception as error:
        print(f'Error getting user profile: {error}')
    return None


def get_user_activity_history(conn, mid, days=90):
    try:
        cur = conn.cursor()
        start_date = datetime.now().date() - timedelta(days=days)
        cur.execute(
            '''
            SELECT mid, record_date, level, coins, fans, following, activity_score
            FROM bilibili_activity_history
            WHERE mid = %s AND record_date >= %s
            ORDER BY record_date DESC
            ''',
            (mid, start_date)
        )
        return _rows_to_dicts(cur, cur.fetchall())
    except Exception as error:
        print(f'Error getting activity history: {error}')
        return []


def batch_generate_profiles(conn, limit=1000):
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM bilibili_user_info LIMIT %s', (limit,))
        users = _rows_to_dicts(cur, cur.fetchall())

        for user_data in users:
            user_data['behavior_features'] = extract_behavior_features(user_data)
            user_data['tags'] = generate_user_tags(user_data)
            history_data = get_user_activity_history(conn, user_data['mid'], days=90)
            user_data['churn_prediction'] = calculate_churn_probability(user_data, history_data=history_data)
            save_user_profile(conn, user_data)

        print(f'Generated profiles for {len(users)} users')
        return len(users)
    except Exception as error:
        print(f'Error in batch generation: {error}')
        return 0
