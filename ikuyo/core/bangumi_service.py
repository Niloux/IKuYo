#!/usr/bin/env python3
"""
Bangumi API服务层
专注于两个核心业务：每日放送和番剧详情
支持多层缓存机制：内存缓存 + 文件缓存
"""

from typing import Any, Dict, List, Optional

import requests

from .cache_service import CacheManager
from .config import load_config


class BangumiService:
    """Bangumi API服务类"""

    def __init__(self):
        config = load_config()
        self.base_url = getattr(config.bangumi, "base_url", "https://api.bgm.tv")
        self.timeout = getattr(config.bangumi, "timeout", 10)
        self.user_agent = getattr(config.bangumi, "user_agent", "IKuYo/2.0.0")

        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        # 初始化缓存管理器
        self.cache = CacheManager()

    def get_calendar(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取每日放送
        为首页提供新番时间表
        使用1小时缓存
        """
        cache_key = "bangumi_calendar"

        # 1. 尝试从缓存获取
        cached_data = self.cache.get(cache_key, "calendar")
        if cached_data is not None:
            print("✅ 从缓存获取每日放送数据")
            return cached_data

        # 2. 缓存未命中，请求API
        try:
            print("🌐 请求Bangumi API获取每日放送...")
            url = f"{self.base_url}/calendar"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # 3. 存入缓存
            self.cache.set(cache_key, data, "calendar")
            print("💾 每日放送数据已缓存，有效期：1小时")

            return data
        except Exception as e:
            print(f"获取每日放送失败: {e}")
            return None

    def get_subject_info(self, bangumi_id: int) -> Optional[Dict[str, Any]]:
        """
        获取番剧详情
        为详情页提供元数据补充
        使用24小时缓存
        """
        cache_key = f"bangumi_subject_{bangumi_id}"

        # 1. 尝试从缓存获取
        cached_data = self.cache.get(cache_key, "subject")
        if cached_data is not None:
            print(f"✅ 从缓存获取番剧详情 (ID: {bangumi_id})")
            return cached_data

        # 2. 缓存未命中，请求API
        try:
            print(f"🌐 请求Bangumi API获取番剧详情 (ID: {bangumi_id})...")
            url = f"{self.base_url}/v0/subjects/{bangumi_id}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # 3. 存入缓存
            self.cache.set(cache_key, data, "subject")
            print(f"💾 番剧详情已缓存 (ID: {bangumi_id})，有效期：24小时")

            return data
        except Exception as e:
            print(f"获取番剧详情失败 (bangumi_id={bangumi_id}): {e}")
            return None

    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """
        清理缓存
        可选择清理特定缓存或全部缓存
        """
        self.cache.clear(cache_key)
        if cache_key:
            print(f"🗑️ 已清理缓存: {cache_key}")
        else:
            print("🗑️ 已清理全部缓存")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self.cache.get_cache_info()


# 全局服务实例
bangumi_service = BangumiService()
