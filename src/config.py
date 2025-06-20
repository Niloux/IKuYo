"""
Mikan爬虫配置文件
"""

import os

# 确保数据目录存在
os.makedirs("data/database", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/output", exist_ok=True)

# 爬虫基础配置
CRAWLER_CONFIG = {
    # 测试模式：限制爬取数量（用于开发和测试）
    "test_mode": True,
    "test_limit": 3,
    # 请求延迟（秒）
    "download_delay": 0.1,
    # 并发请求数
    "concurrent_requests": 32,
    # 重试次数
    "retry_times": 3,
}

# 网站配置
SITE_CONFIG = {
    "base_url": "https://mikanani.me",
    "allowed_domains": ["mikanani.me"],
    "start_urls": ["https://mikanani.me/Home"],
}

# 爬取模式配置
CRAWL_MODE_CONFIG = {
    # 爬取模式：homepage(首页), year(年份), season(季度), full(全量), incremental(增量)
    "mode": "season",
    # 指定年份（年份模式或季度模式时使用）
    "year": 2024,
    # 指定季度（季度模式时使用）：春、夏、秋、冬
    "season": "夏",
    # 年份范围（全量模式时使用）
    "year_range": {"start": 2013, "end": 2025},
    # 季度列表
    "seasons": ["春", "夏", "秋", "冬"],
    # 增量爬取配置
    "incremental": {
        "enabled": False,
        "last_crawl_time": None,
        "check_interval": 3600,  # 1小时
    },
    # API接口配置
    "api": {
        "enabled": True,
        "timeout": 30,
        "retry_times": 3,
    },
    # 动态页面解析配置（API失败时的降级方案）
    "dynamic_parser": {
        "enabled": True,
        "wait_time": 3,  # 等待页面加载时间
        "timeout": 60,
    },
}

# 数据库配置
DATABASE_CONFIG = {
    "sqlite_db": "data/database/ikuyo.db",
}

# 输出配置
OUTPUT_CONFIG = {
    "output_dir": "output",
}

# 定时任务配置
SCHEDULER_CONFIG = {
    # 是否启用定时任务
    "enabled": True,
    # 默认调度时间 (每天凌晨2点执行)
    "default_cron": "0 2 * * *",
    # 时区设置
    "timezone": "Asia/Shanghai",
    # 任务配置
    "jobs": [
        {
            "id": "mikan_crawler",
            "name": "Mikan爬虫定时任务",
            "cron": "0 2 * * *",  # 每天凌晨2点
            "enabled": True,
            "description": "定时爬取Mikan Project动画资源",
            "mode": "homepage",  # 默认首页模式
        }
    ],
    # 调度器设置
    "scheduler_settings": {
        "job_defaults": {
            "coalesce": False,
            "max_instances": 1,
            "misfire_grace_time": 300,  # 5分钟容错时间
        }
    },
}


def get_config(section, key=None):
    """获取配置值"""
    configs = {
        "crawler": CRAWLER_CONFIG,
        "site": SITE_CONFIG,
        "crawl_mode": CRAWL_MODE_CONFIG,
        "database": DATABASE_CONFIG,
        "output": OUTPUT_CONFIG,
        "scheduler": SCHEDULER_CONFIG,
    }

    if section not in configs:
        raise ValueError(f"Unknown config section: {section}")

    if key is None:
        return configs[section]

    if key not in configs[section]:
        raise ValueError(f"Unknown config key: {key} in section: {section}")

    return configs[section][key]


def is_test_mode():
    """检查是否为测试模式"""
    return get_config("crawler", "test_mode")


def get_test_limit():
    """获取测试模式下的限制数量"""
    return get_config("crawler", "test_limit")


def get_crawl_mode():
    """获取当前爬取模式"""
    return get_config("crawl_mode", "mode")


def get_crawl_year():
    """获取爬取年份"""
    return get_config("crawl_mode", "year")


def get_crawl_season():
    """获取爬取季度"""
    return get_config("crawl_mode", "season")


def get_year_range():
    """获取年份范围"""
    return get_config("crawl_mode", "year_range")


def get_seasons():
    """获取季度列表"""
    return get_config("crawl_mode", "seasons")
