#!/usr/bin/env python3
"""
Bangumi API服务层
专注于两个核心业务：每日放送和番剧详情
"""

from typing import Any, Dict, List, Optional

import requests

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

    def get_calendar(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取每日放送
        为首页提供新番时间表
        """
        try:
            url = f"{self.base_url}/calendar"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取每日放送失败: {e}")
            return None

    def get_subject_info(self, bangumi_id: int) -> Optional[Dict[str, Any]]:
        """
        获取番剧详情
        为详情页提供元数据补充
        """
        try:
            url = f"{self.base_url}/v0/subjects/{bangumi_id}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取番剧详情失败 (bangumi_id={bangumi_id}): {e}")
            return None


# 全局服务实例
bangumi_service = BangumiService()
