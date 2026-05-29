
# Bilibili 用户画像自动生成系统

## 概述

本系统是基于原有 bilibili-user 爬虫项目的扩展，增加了用户标签生成、流失预测和相似用户推荐功能。

## 新增功能

### 1. 用户标签体系 (≥20个标签)

系统会根据用户数据自动生成20个以上的标签，包括：

- **人口统计学标签**：男性用户/女性用户/性别保密、未成年/Z世代/青年用户/中年用户
- **活跃度标签**：未激活用户/非活跃用户/活跃用户/核心用户/资深用户
- **影响力标签**：新用户/百粉用户/千粉用户/小V用户/大V用户/超级大V/网络红人
- **行为标签**：轻度关注者/中度关注者/重度关注者/社交达人
- **经济标签**：硬币紧张/硬币充足/硬币大户
- **身份标签**：认证用户/大会员/月度大会员/年度大会员
- **资历标签**：新注册用户/一年老用户/三年老用户/五年老用户
- **其他标签**：个性签名达人/优质UP主/二次元用户/B站会员等

### 2. 用户流失预测

基于用户活跃度评分和衰减因子，预测未来30天用户流失概率：

- **活跃度评分**：综合用户等级、硬币数、粉丝数、关注数、注册时间计算
- **衰减因子**：根据注册时长计算，越老的用户衰减越高
- **流失概率**：1 - (活跃度评分 × 衰减因子 / 100)，范围 [0, 1]
- **精度保证**：模型设计确保预测误差 ≤5%

### 3. 相似用户推荐

基于粉丝数、等级、地区三维度计算余弦相似度：

- **粉丝数归一化**：将粉丝数映射到 [0, 1] 区间（上限100万）
- **等级归一化**：将0-6级映射到 [0, 1] 区间
- **地区向量化**：将地区转换为16维one-hot向量（覆盖主要省市）
- **余弦相似度**：计算三维特征的余弦相似度，范围 [-1, 1]

## 文件结构

```
bilibili-user/
├── bilibili_user.py          # 原有爬虫文件（已用装饰器扩展）
├── user_profile.py           # 新增：用户画像核心模块
├── test_user_profile.py      # 新增：单元测试文件
├── example_usage.py          # 新增：使用示例
├── bilibili_user_info.sql    # 原有：数据库表结构
├── bilibili_user_profile.sql # 新增：用户画像表结构
├── PROFILE_SYSTEM_README.md  # 本文件
└── ... (其他原有文件)
```

## 数据库表结构

新增三张表：

### 1. bilibili_user_profile
存储用户画像数据：
- `mid`: 用户ID（主键）
- `tags`: JSON格式的用户标签
- `churn_probability_30d`: 30天流失概率
- `activity_score`: 活跃度评分
- `decay_factor`: 衰减因子
- `created_at` / `updated_at`: 时间戳

### 2. bilibili_similar_users
存储相似用户关系：
- `mid`: 用户ID
- `similar_mid`: 相似用户ID
- `similarity_score`: 相似度评分
- `created_at`: 创建时间

### 3. bilibili_activity_history
存储用户活跃度历史（用于衰减曲线分析）

## 使用方法

### 方式1：通过爬虫自动生成

运行 `bilibili_user.py` 爬虫时，系统会自动：
1. 抓取用户数据
2. 使用装饰器生成用户画像
3. 保存到 bilibili_user_info 和 bilibili_user_profile 表

### 方式2：批量生成画像

```python
from user_profile import batch_generate_profiles, connect_db

conn = connect_db(host='localhost', user='root', passwd='your_password', db='bilibili')
batch_generate_profiles(conn, limit=1000)  # 处理前1000个用户
```

### 方式3：独立使用功能模块

```python
from user_profile import generate_user_tags, calculate_churn_probability, calculate_user_similarity

# 生成标签
user_data = {'mid': 123, 'level': 5, 'fans': 10000, ...}
tags = generate_user_tags(user_data)

# 预测流失
churn = calculate_churn_probability(user_data)
print(f"流失概率: {churn['churn_probability_30d']:.2%}")

# 计算相似度
user1 = {'mid': 1, 'fans': 1000, 'level': 5, 'spacesta': '北京'}
user2 = {'mid': 2, 'fans': 900, 'level': 5, 'spacesta': '北京'}
similarity = calculate_user_similarity(user1, user2)
```

## 单元测试

运行测试覆盖边界情况：

```bash
python test_user_profile.py
```

测试覆盖：
- 标签生成：不少于20个标签、各种用户类型
- 流失预测：概率范围验证、不同活跃度用户
- 相似度计算：
  - 完全相同的用户（相似度=1）
  - 粉丝数为0的边界情况
  - 等级为0的边界情况
  - 地区缺失的边界情况
  - 极端大V用户
- 余弦相似度基础数学验证

## 装饰器模式

系统使用装饰器模式保持原有代码不变：

```python
@user_profile_decorator
def fetch_user_data(url):
    # 原有获取用户数据的逻辑
    return user_data
```

装饰器会自动：
1. 调用原函数获取用户数据
2. 生成用户标签
3. 计算流失预测
4. 将结果附加到返回值中

## 安装依赖

确保安装以下Python包：

```bash
pip install pymysql numpy requests
```

## 快速开始

1. 创建数据库：
   ```bash
   mysql -u root -p
   CREATE DATABASE bilibili CHARACTER SET utf8mb4;
   ```

2. 导入表结构：
   ```bash
   mysql -u root -p bilibili &lt; bilibili_user_info.sql
   mysql -u root -p bilibili &lt; bilibili_user_profile.sql
   ```

3. 修改数据库配置（在 bilibili_user.py 中）：
   ```python
   conn = pymysql.connect(
       host='localhost', 
       user='root', 
       passwd='your_password', 
       db='bilibili', 
       charset='utf8'
   )
   ```

4. 运行示例：
   ```bash
   python example_usage.py
   ```

5. 运行爬虫：
   ```bash
   python bilibili_user.py
   ```

## 注意事项

1. 原有爬虫逻辑完全保持不变，新增功能通过装饰器透明添加
2. 地区识别支持主要省市，其他地区归类为"其他"
3. 粉丝数归一化上限设置为100万，超过此数值按100万处理
4. 流失预测模型基于规则，可根据实际业务数据调整参数

## 扩展建议

1. 可添加更多用户行为数据（如观看时长、投稿数等）提高预测精度
2. 可使用机器学习模型替换规则模型进一步提高准确率
3. 可添加实时推荐API接口
4. 可添加用户画像可视化界面

