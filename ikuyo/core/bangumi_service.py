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

    def get_episodes(
        self,
        subject_id: int,
        episode_type: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        获取番剧章节信息
        为章节展示提供数据
        使用12小时缓存

        Args:
            subject_id: 番剧ID
            episode_type: 章节类型筛选 (0:正片, 1:SP, 2:OP, 3:ED, 4:PV, 6:其他)
            limit: 返回数量限制
            offset: 偏移量
        """
        # 构建缓存键，包含筛选参数
        type_suffix = f"_type_{episode_type}" if episode_type is not None else ""
        cache_key = f"bangumi_episodes_{subject_id}{type_suffix}_{limit}_{offset}"

        # 1. 尝试从缓存获取
        cached_data = self.cache.get(cache_key, "episodes")
        if cached_data is not None:
            print(f"✅ 从缓存获取章节信息 (subject_id: {subject_id})")
            return cached_data

        # 2. 缓存未命中，请求API
        try:
            print(f"🌐 请求Bangumi API获取章节信息 (subject_id: {subject_id})...")

            # 构建请求参数
            params = {"subject_id": subject_id, "limit": limit, "offset": offset}
            if episode_type is not None:
                params["type"] = episode_type

            url = f"{self.base_url}/v0/episodes"
            response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # 3. API返回的数据结构处理
            episodes_data = {
                "data": data.get("data", []),
                "total": data.get("total", 0),
                "limit": data.get("limit", limit),
                "offset": data.get("offset", offset),
            }

            # 4. 存入缓存 (12小时)
            self.cache.set(cache_key, episodes_data, "episodes")
            print(f"💾 章节信息已缓存 (subject_id: {subject_id})，有效期：12小时")

            return episodes_data
        except Exception as e:
            print(f"获取章节信息失败 (subject_id={subject_id}): {e}")
            return None

    def get_episodes_stats(self, subject_id: int) -> Optional[Dict[str, Any]]:
        """
        获取番剧章节统计信息
        统计各类型章节数量
        使用12小时缓存
        """
        cache_key = f"bangumi_episodes_stats_{subject_id}"

        # 1. 尝试从缓存获取
        cached_data = self.cache.get(cache_key, "episodes")
        if cached_data is not None:
            print(f"✅ 从缓存获取章节统计 (subject_id: {subject_id})")
            return cached_data

        # 2. 获取所有章节数据
        episodes_data = self.get_episodes(subject_id, limit=1000)  # 获取足够多的章节
        if not episodes_data:
            return None

        # 3. 统计各类型章节数量
        episodes = episodes_data.get("data", [])
        stats = {
            "total": len(episodes),
            "main_episodes": 0,  # type 0: 正片
            "special_episodes": 0,  # type 1: SP
            "opening_episodes": 0,  # type 2: OP
            "ending_episodes": 0,  # type 3: ED
            "pv_episodes": 0,  # type 4: PV
            "other_episodes": 0,  # type 6: 其他
        }

        for episode in episodes:
            episode_type = episode.get("type", 0)
            if episode_type == 0:
                stats["main_episodes"] += 1
            elif episode_type == 1:
                stats["special_episodes"] += 1
            elif episode_type == 2:
                stats["opening_episodes"] += 1
            elif episode_type == 3:
                stats["ending_episodes"] += 1
            elif episode_type == 4:
                stats["pv_episodes"] += 1
            else:
                stats["other_episodes"] += 1

        # 4. 存入缓存
        self.cache.set(cache_key, stats, "episodes")
        print(f"💾 章节统计已缓存 (subject_id: {subject_id})，有效期：12小时")

        return stats

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
