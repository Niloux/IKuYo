"""
IKuYo - 动漫资源爬虫
面向追番爱好者的智能动漫资源采集工具
"""

__version__ = "0.1.0"
__author__ = "wuyou"
__description__ = "动画爬虫，获取种子资源"

# 导出核心模块
from . import core, crawler, utils

__all__ = ["core", "crawler", "utils"]
