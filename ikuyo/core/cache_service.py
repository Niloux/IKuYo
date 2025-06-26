#!/usr/bin/env python3
"""
缓存服务模块
提供多层缓存机制：内存缓存 + 文件缓存
"""

import json
import os
import time
from typing import Any, Dict, Optional


class CacheManager:
    """
    多层缓存管理器
    - 内存缓存：快速访问
    - 文件缓存：持久化存储
    - TTL机制：自动过期
    """

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)

        # 缓存配置：不同数据类型的过期时间（秒）
        self.cache_ttl = {
            "calendar": 3600,  # 每日放送：1小时
            "subject": 86400,  # 番剧详情：24小时
            "episodes": 43200,  # 章节信息：12小时
            "default": 1800,  # 默认：30分钟
        }

    def _get_cache_file(self, key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{key}.json")

    def _is_expired(self, cache_data: Dict[str, Any], cache_type: str = "default") -> bool:
        """检查缓存是否过期"""
        if "timestamp" not in cache_data:
            return True

        ttl = self.cache_ttl.get(cache_type, self.cache_ttl["default"])
        cache_time = cache_data["timestamp"]
        return time.time() - cache_time > ttl

    def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """
        获取缓存数据
        优先从内存缓存获取，其次文件缓存
        """
        # 1. 检查内存缓存
        if key in self.memory_cache:
            cache_data = self.memory_cache[key]
            if not self._is_expired(cache_data, cache_type):
                return cache_data["data"]
            else:
                # 内存缓存过期，删除
                del self.memory_cache[key]

        # 2. 检查文件缓存
        cache_file = self._get_cache_file(key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                if not self._is_expired(cache_data, cache_type):
                    # 文件缓存有效，加载到内存
                    self.memory_cache[key] = cache_data
                    return cache_data["data"]
                else:
                    # 文件缓存过期，删除
                    os.remove(cache_file)
            except Exception as e:
                print(f"读取缓存文件失败 {cache_file}: {e}")
                # 删除损坏的缓存文件
                try:
                    os.remove(cache_file)
                except:
                    pass

        return None

    def set(self, key: str, data: Any, cache_type: str = "default") -> None:
        """
        设置缓存数据
        同时写入内存和文件
        """
        cache_data = {"data": data, "timestamp": time.time(), "cache_type": cache_type}

        # 1. 写入内存缓存
        self.memory_cache[key] = cache_data

        # 2. 写入文件缓存
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入缓存文件失败 {cache_file}: {e}")

    def clear(self, key: Optional[str] = None) -> None:
        """
        清理缓存
        如果指定key则只清理特定缓存，否则清理全部
        """
        if key:
            # 清理特定缓存
            if key in self.memory_cache:
                del self.memory_cache[key]

            cache_file = self._get_cache_file(key)
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                except Exception as e:
                    print(f"删除缓存文件失败 {cache_file}: {e}")
        else:
            # 清理全部缓存
            self.memory_cache.clear()

            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith(".json"):
                        os.remove(os.path.join(self.cache_dir, filename))
            except Exception as e:
                print(f"清理缓存目录失败: {e}")

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        memory_count = len(self.memory_cache)

        file_count = 0
        try:
            file_count = len([f for f in os.listdir(self.cache_dir) if f.endswith(".json")])
        except:
            pass

        return {
            "memory_cache_count": memory_count,
            "file_cache_count": file_count,
            "cache_ttl_config": self.cache_ttl,
        }
