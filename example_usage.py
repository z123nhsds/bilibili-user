
# -*-coding:utf8-*-

from user_profile import (
    generate_user_tags,
    calculate_churn_probability,
    calculate_user_similarity,
    find_similar_users,
    batch_generate_profiles,
    connect_db
)

def example_tag_generation():
    print("=== Example 1: User Tag Generation ===")
    
    sample_users = [
        {
            'mid': 10001,
            'name': '科技达人小王',
            'sex': '男',
            'level': 6,
            'coins': 50000,
            'fans': 2000000,
            'following': 150,
            'birthday': '1995-03-15',
            'sign': '科技改变生活，创新引领未来',
            'regtime': '2016-05-20 10:30:00',
            'OfficialVerifyType': 1,
            'vipType': 2,
            'vipStatus': 1,
            'spacesta': '北京'
        },
        {
            'mid': 10002,
            'name': '萌新小红',
            'sex': '女',
            'level': 1,
            'coins': 50,
            'fans': 5,
            'following': 30,
            'birthday': '2005-08-20',
            'sign': '刚注册B站，请多关照！',
            'regtime': '2024-01-15 18:45:00',
            'OfficialVerifyType': 0,
            'vipType': 0,
            'vipStatus': 0,
            'spacesta': '上海'
        },
        {
            'mid': 10003,
            'name': '神秘用户',
            'sex': '保密',
            'level': 0,
            'coins': 0,
            'fans': 0,
            'following': 0,
            'birthday': 'nobirthday',
            'sign': '',
            'regtime': '2015-02-28 00:00:00',
            'OfficialVerifyType': 0,
            'vipType': 0,
            'vipStatus': 0,
            'spacesta': ''
        }
    ]
    
    for user in sample_users:
        tags = generate_user_tags(user)
        print(f"\nUser: {user['name']} (mid: {user['mid']})")
        print(f"Generated {len(tags)} tags:")
        for i, tag in enumerate(tags, 1):
            print(f"  {i}. {tag}")


def example_churn_prediction():
    print("\n=== Example 2: Churn Probability Prediction ===")
    
    user_profiles = [
        {
            'mid': 20001,
            'name': '高活跃用户',
            'level': 6,
            'coins': 100000,
            'fans': 500000,
            'following': 500,
            'regtime': '2018-01-01 00:00:00'
        },
        {
            'mid': 20002,
            'name': '中活跃用户',
            'level': 3,
            'coins': 1000,
            'fans': 500,
            'following': 100,
            'regtime': '2020-06-15 00:00:00'
        },
        {
            'mid': 20003,
            'name': '低活跃用户',
            'level': 0,
            'coins': 0,
            'fans': 0,
            'following': 0,
            'regtime': '2015-03-10 00:00:00'
        }
    ]
    
    for user in user_profiles:
        prediction = calculate_churn_probability(user)
        print(f"\nUser: {user['name']}")
        print(f"  30天流失概率: {prediction['churn_probability_30d']:.2%}")
        print(f"  活跃度评分: {prediction['activity_score']:.2f}")
        print(f"  衰减因子: {prediction['decay_factor']:.2f}")
        print(f"  注册天数: {prediction['days_since_registration']}")


def example_similar_users():
    print("\n=== Example 3: Similar Users Recommendation ===")
    
    user_database = [
        {'mid': 30001, 'name': '用户A', 'fans': 10000, 'level': 5, 'spacesta': '北京'},
        {'mid': 30002, 'name': '用户B', 'fans': 8000, 'level': 5, 'spacesta': '北京'},
        {'mid': 30003, 'name': '用户C', 'fans': 10000, 'level': 4, 'spacesta': '上海'},
        {'mid': 30004, 'name': '用户D', 'fans': 500, 'level': 2, 'spacesta': '广东'},
        {'mid': 30005, 'name': '用户E', 'fans': 15000, 'level': 6, 'spacesta': '北京'},
        {'mid': 30006, 'name': '用户F', 'fans': 0, 'level': 0, 'spacesta': ''},
        {'mid': 30007, 'name': '用户G', 'fans': 0, 'level': 0, 'spacesta': ''},
    ]
    
    target_user = {'mid': 99999, 'name': '目标用户', 'fans': 10000, 'level': 5, 'spacesta': '北京'}
    similar = find_similar_users(target_user, user_database, top_n=5)
    
    print(f"Target User: {target_user['name']}")
    print(f"  Fans: {target_user['fans']}, Level: {target_user['level']}, Region: {target_user['spacesta']}")
    print("\nTop 5 Similar Users:")
    for i, (user, similarity) in enumerate(similar, 1):
        print(f"  {i}. {user['name']} (mid: {user['mid']})")
        print(f"     Similarity: {similarity:.4f}")
        print(f"     Fans: {user['fans']}, Level: {user['level']}, Region: {user['spacesta']}")
    
    print("\n=== Boundary Case Tests ===")
    user_zero = {'mid': 40001, 'fans': 0, 'level': 0, 'spacesta': ''}
    user_another_zero = {'mid': 40002, 'fans': 0, 'level': 0, 'spacesta': ''}
    sim = calculate_user_similarity(user_zero, user_another_zero)
    print(f"Similarity between zero-value users: {sim:.4f}")


def example_batch_processing():
    print("\n=== Example 4: Batch Profile Generation ===")
    print("This example demonstrates how to generate profiles for multiple users.")
    print("Note: Requires a connected MySQL database with bilibili_user_info table.")
    print("\nTo use batch processing:")
    print("1. Ensure MySQL is running and bilibili database exists")
    print("2. Run bilibili_user_profile.sql to create required tables")
    print("3. Call batch_generate_profiles(conn, limit=1000) to process users")


if __name__ == '__main__':
    print("=" * 60)
    print("Bilibili User Profile System - Usage Examples")
    print("=" * 60)
    
    example_tag_generation()
    example_churn_prediction()
    example_similar_users()
    example_batch_processing()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)

