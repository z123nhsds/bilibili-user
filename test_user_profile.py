
# -*-coding:utf8-*-

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from user_profile import (
    generate_user_tags,
    calculate_churn_probability,
    cosine_similarity,
    calculate_user_similarity,
    find_similar_users,
    get_region_vector
)


class TestUserProfile(unittest.TestCase):

    def test_generate_user_tags_min_20(self):
        user_data = {
            'mid': 12345,
            'name': 'test_user',
            'sex': '男',
            'level': 5,
            'coins': 10000,
            'fans': 50000,
            'following': 200,
            'birthday': '1995-05-20',
            'sign': '这是一个很长很长很长的个性签名，用来测试个性签名达人标签',
            'regtime': '2018-01-01 12:00:00',
            'OfficialVerifyType': 1,
            'vipType': 2,
            'vipStatus': 1
        }
        
        tags = generate_user_tags(user_data)
        self.assertGreaterEqual(len(tags), 20)
        print(f"Generated {len(tags)} tags: {tags}")

    def test_generate_user_tags_female_user(self):
        user_data = {
            'mid': 12346,
            'name': 'female_user',
            'sex': '女',
            'level': 3,
            'coins': 500,
            'fans': 100,
            'following': 50
        }
        
        tags = generate_user_tags(user_data)
        self.assertIn('女性用户', tags)

    def test_generate_user_tags_secret_sex(self):
        user_data = {
            'mid': 12347,
            'name': 'secret_user',
            'sex': '保密',
            'level': 2,
            'coins': 100,
            'fans': 10,
            'following': 20
        }
        
        tags = generate_user_tags(user_data)
        self.assertIn('性别保密', tags)

    def test_generate_user_tags_super_vip(self):
        user_data = {
            'mid': 12348,
            'name': 'super_vip',
            'sex': '男',
            'level': 6,
            'coins': 50000,
            'fans': 2000000,
            'following': 100
        }
        
        tags = generate_user_tags(user_data)
        self.assertIn('超级大V', tags)

    def test_calculate_churn_probability_range(self):
        user_data = {
            'mid': 23456,
            'level': 5,
            'coins': 10000,
            'fans': 50000,
            'following': 200,
            'regtime': '2020-01-01 12:00:00'
        }
        
        result = calculate_churn_probability(user_data)
        self.assertGreaterEqual(result['churn_probability_30d'], 0.0)
        self.assertLessEqual(result['churn_probability_30d'], 1.0)
        self.assertGreater(result['activity_score'], 0)
        print(f"Churn prediction: {result}")

    def test_calculate_churn_probability_inactive_user(self):
        user_data = {
            'mid': 23457,
            'level': 0,
            'coins': 0,
            'fans': 0,
            'following': 0,
            'regtime': '2015-01-01 12:00:00'
        }
        
        result = calculate_churn_probability(user_data)
        self.assertGreater(result['churn_probability_30d'], 0.5)

    def test_cosine_similarity_identical(self):
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        sim = cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, 1.0, places=4)

    def test_cosine_similarity_opposite(self):
        vec1 = [1.0, 0.0]
        vec2 = [-1.0, 0.0]
        sim = cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, -1.0, places=4)

    def test_cosine_similarity_orthogonal(self):
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        sim = cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, 0.0, places=4)

    def test_cosine_similarity_zero_vector(self):
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        sim = cosine_similarity(vec1, vec2)
        self.assertEqual(sim, 0.0)

    def test_calculate_user_similarity_identical(self):
        user1 = {'mid': 1, 'fans': 1000, 'level': 5, 'spacesta': '北京'}
        user2 = {'mid': 2, 'fans': 1000, 'level': 5, 'spacesta': '北京'}
        sim = calculate_user_similarity(user1, user2)
        self.assertAlmostEqual(sim, 1.0, places=4)

    def test_calculate_user_similarity_zero_fans(self):
        user1 = {'mid': 1, 'fans': 0, 'level': 0, 'spacesta': ''}
        user2 = {'mid': 2, 'fans': 0, 'level': 0, 'spacesta': ''}
        sim = calculate_user_similarity(user1, user2)
        self.assertGreaterEqual(sim, 0.0)
        self.assertLessEqual(sim, 1.0)
        print(f"Similarity with zero fans: {sim}")

    def test_calculate_user_similarity_level_zero(self):
        user1 = {'mid': 1, 'fans': 500, 'level': 0, 'spacesta': '上海'}
        user2 = {'mid': 2, 'fans': 500, 'level': 0, 'spacesta': '上海'}
        sim = calculate_user_similarity(user1, user2)
        self.assertGreater(sim, 0.5)

    def test_calculate_user_similarity_region_missing(self):
        user1 = {'mid': 1, 'fans': 1000, 'level': 3, 'spacesta': ''}
        user2 = {'mid': 2, 'fans': 1000, 'level': 3, 'spacesta': ''}
        sim = calculate_user_similarity(user1, user2)
        self.assertGreater(sim, 0.5)
        print(f"Similarity with missing region: {sim}")

    def test_calculate_user_similarity_different_regions(self):
        user1 = {'mid': 1, 'fans': 1000, 'level': 3, 'spacesta': '北京'}
        user2 = {'mid': 2, 'fans': 1000, 'level': 3, 'spacesta': '上海'}
        sim = calculate_user_similarity(user1, user2)
        self.assertLess(sim, 1.0)
        self.assertGreater(sim, 0.0)

    def test_calculate_user_similarity_extreme_fans(self):
        user1 = {'mid': 1, 'fans': 10000000, 'level': 6, 'spacesta': '广东'}
        user2 = {'mid': 2, 'fans': 10000000, 'level': 6, 'spacesta': '广东'}
        sim = calculate_user_similarity(user1, user2)
        self.assertAlmostEqual(sim, 1.0, places=4)

    def test_find_similar_users(self):
        target_user = {'mid': 1, 'fans': 1000, 'level': 5, 'spacesta': '北京'}
        all_users = [
            {'mid': 1, 'fans': 1000, 'level': 5, 'spacesta': '北京'},
            {'mid': 2, 'fans': 900, 'level': 5, 'spacesta': '北京'},
            {'mid': 3, 'fans': 500, 'level': 3, 'spacesta': '上海'},
            {'mid': 4, 'fans': 100, 'level': 2, 'spacesta': '广东'},
            {'mid': 5, 'fans': 2000, 'level': 6, 'spacesta': '北京'}
        ]
        
        similar = find_similar_users(target_user, all_users, top_n=3)
        self.assertEqual(len(similar), 3)
        self.assertNotEqual(similar[0][0]['mid'], 1)
        print(f"Found similar users: {[(u['mid'], s) for u, s in similar]}")

    def test_get_region_vector(self):
        vec = get_region_vector('北京')
        self.assertEqual(len(vec), 16)
        self.assertEqual(vec[0], 1.0)
        
        vec = get_region_vector('上海')
        self.assertEqual(vec[1], 1.0)
        
        vec = get_region_vector('未知地区')
        self.assertEqual(vec[-1], 1.0)
        
        vec = get_region_vector('')
        self.assertEqual(vec[-1], 1.0)

    def test_full_workflow(self):
        user_data = {
            'mid': 99999,
            'name': 'workflow_test',
            'sex': '女',
            'level': 4,
            'coins': 5000,
            'fans': 5000,
            'following': 300,
            'birthday': '1998-08-08',
            'sign': '热爱生活，热爱B站',
            'regtime': '2019-06-01 10:00:00',
            'OfficialVerifyType': 0,
            'vipType': 1,
            'vipStatus': 1
        }
        
        tags = generate_user_tags(user_data)
        churn = calculate_churn_probability(user_data)
        
        self.assertGreaterEqual(len(tags), 20)
        self.assertGreaterEqual(churn['churn_probability_30d'], 0.0)
        self.assertLessEqual(churn['churn_probability_30d'], 1.0)
        
        print("\n=== Full Workflow Test ===")
        print(f"Tags: {tags}")
        print(f"Churn Prediction: {churn}")


if __name__ == '__main__':
    unittest.main(verbosity=2)

