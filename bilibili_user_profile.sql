
-- 用户画像表结构
-- 用于存储用户标签、流失预测等画像数据

DROP TABLE IF EXISTS `bilibili_user_profile`;
CREATE TABLE `bilibili_user_profile` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `mid` int(20) unsigned NOT NULL UNIQUE,
  `tags` text NOT NULL,
  `churn_probability_30d` decimal(10,4) NOT NULL DEFAULT 0.0000,
  `activity_score` decimal(10,2) NOT NULL DEFAULT 0.00,
  `decay_factor` decimal(10,2) NOT NULL DEFAULT 1.00,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_mid` (`mid`),
  KEY `idx_churn` (`churn_probability_30d`),
  KEY `idx_activity` (`activity_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 相似用户推荐历史表
DROP TABLE IF EXISTS `bilibili_similar_users`;
CREATE TABLE `bilibili_similar_users` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `mid` int(20) unsigned NOT NULL,
  `similar_mid` int(20) unsigned NOT NULL,
  `similarity_score` decimal(10,6) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_mid` (`mid`),
  KEY `idx_similarity` (`similarity_score`),
  UNIQUE KEY `idx_pair` (`mid`, `similar_mid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户活跃度历史表（用于追踪衰减曲线）
DROP TABLE IF EXISTS `bilibili_activity_history`;
CREATE TABLE `bilibili_activity_history` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `mid` int(20) unsigned NOT NULL,
  `record_date` date NOT NULL,
  `level` int(1) unsigned NOT NULL,
  `coins` int(20) unsigned NOT NULL,
  `fans` int(20) unsigned NOT NULL,
  `following` int(20) unsigned NOT NULL,
  `activity_score` decimal(10,2) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_mid_date` (`mid`, `record_date`),
  KEY `idx_date` (`record_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

