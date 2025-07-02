#!/usr/bin/env python3
"""
Bangumi API 服务模块
提供对 Bangumi.tv API 的封装，包括缓存机制
"""

from typing import Any, Dict, List, Optional

import httpx

from .cache_service import CacheManager


class BangumiService:
    """Bangumi API 服务"""

    def __init__(self):
        self.base_url = "https://api.bgm.tv"
        self.cache = CacheManager()

    async def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """发起HTTP请求"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"请求失败 {url}: {e}")
            return None

    async def get_calendar(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取每日放送数据
        优先从缓存获取，缓存失效时从API获取
        """
        cache_key = "bangumi_calendar"

        # 尝试从缓存获取
        cached_data = self.cache.get(cache_key, "calendar")
        if cached_data:
            print("📦 从缓存获取每日放送数据")
            return cached_data

        # 从API获取新数据
        print("🌐 从API获取每日放送数据")
        url = f"{self.base_url}/calendar"

        api_data = await self._make_request(url)
        if api_data and isinstance(api_data, list):
            self.cache.set(cache_key, api_data, "calendar")
            print("✅ 每日放送数据已缓存")
            return api_data

        return None

    async def get_subject(self, subject_id: int) -> Optional[Dict[str, Any]]:
        """
        获取番剧详情
        优先从缓存获取，缓存失效时从API获取
        """
        cache_key = f"bangumi_subject_{subject_id}"

        # 尝试从缓存获取
        cached_data = self.cache.get(cache_key, "subject")
        if cached_data:
            print(f"📦 从缓存获取番剧详情: {subject_id}")
            return cached_data

        # 从API获取新数据
        print(f"🌐 从API获取番剧详情: {subject_id}")
        url = f"{self.base_url}/v0/subjects/{subject_id}"

        api_data = await self._make_request(url)
        if api_data:
            self.cache.set(cache_key, api_data, "subject")
            print(f"✅ 番剧详情已缓存: {subject_id}")
            return api_data

        return None

    async def get_episodes(
        self,
        subject_id: int,
        episode_type: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        获取番剧章节信息
        支持分页获取，对长篇动画至关重要

        Args:
            subject_id: 番剧ID
            episode_type: 章节类型筛选 (0:正片, 1:SP, 2:OP, 3:ED, 4:PV, 6:其他)
            limit: 返回数量限制（长篇动画需要1000）
            offset: 偏移量
        """
        # 构建缓存键，包含筛选参数
        type_suffix = f"_type_{episode_type}" if episode_type is not None else ""
        cache_key = f"bangumi_episodes_{subject_id}{type_suffix}_{limit}_{offset}"

        # 尝试从缓存获取
        cached_data = self.cache.get(cache_key, "episodes")
        if cached_data:
            print(
                f"📦 从缓存获取章节信息: {subject_id} (limit={limit}, offset={offset})"
            )
            return cached_data

        # 从API获取新数据
        print(f"🌐 从API获取章节信息: {subject_id} (limit={limit}, offset={offset})")
        url = f"{self.base_url}/v0/episodes"

        # 构建请求参数
        params = {"subject_id": subject_id, "limit": limit, "offset": offset}
        if episode_type is not None:
            params["type"] = episode_type

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                api_data = response.json()

                # API返回的数据结构处理
                episodes_data = {
                    "data": api_data.get("data", []),
                    "total": api_data.get("total", 0),
                    "limit": api_data.get("limit", limit),
                    "offset": api_data.get("offset", offset),
                }

                # 存入缓存
                self.cache.set(cache_key, episodes_data, "episodes")
                episodes_count = len(episodes_data["data"])
                total_count = episodes_data["total"]
                print(
                    f"✅ 章节信息已缓存: {subject_id} ({episodes_count}/{total_count} 个章节)"
                )

                return episodes_data

        except Exception as e:
            print(f"获取章节信息失败 {subject_id}: {e}")

        return None

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存状态信息"""
        return self.cache.get_cache_info()

    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """清理缓存"""
        self.cache.clear(cache_key)
        if cache_key:
            print(f"✅ 已清理缓存: {cache_key}")
        else:
            print("✅ 已清理全部缓存")
