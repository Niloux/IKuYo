"""
Mikan爬虫配置文件
简化配置，专注于定时任务需求
"""

# 爬虫基础配置
CRAWLER_CONFIG = {
    # 测试模式：限制爬取数量（用于开发和测试）
    "test_mode": True,
    "test_limit": 3,
    # 请求延迟（秒）
    "download_delay": 1,
    # 并发请求数
    "concurrent_requests": 16,
    # 重试次数
    "retry_times": 3,
}

# 网站配置
SITE_CONFIG = {
    "base_url": "https://mikanani.me",
    "allowed_domains": ["mikanani.me"],
    "start_urls": ["https://mikanani.me/Home"],
}

# 数据库配置
DATABASE_CONFIG = {
    "sqlite_db": "data/mikan_data.db",
}

# 输出配置
OUTPUT_CONFIG = {
    "output_dir": "output",
}


def get_config(section, key=None):
    """获取配置值"""
    configs = {
        "crawler": CRAWLER_CONFIG,
        "site": SITE_CONFIG,
        "database": DATABASE_CONFIG,
        "output": OUTPUT_CONFIG,
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
