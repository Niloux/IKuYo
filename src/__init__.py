"""
IKuYo - 动画资源爬虫系统
"""

__version__ = "1.0.0"
__author__ = "IKuYo Team"
__description__ = "基于Scrapy的Mikan Project动画资源爬虫系统"

from .config import Config, load_config

__all__ = ["load_config", "Config"]
