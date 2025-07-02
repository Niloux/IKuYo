#!/usr/bin/env python3
"""
缓存服务模块
提供多层缓存机制：内存缓存 + 文件缓存
基于cachetools实现高性能TTL缓存
"""

import json
import os
import threading
import time
from typing import Any, Dict, Optional

from cachetools import TTLCache

from .config import load_config


class CacheManager:
    """
    多层缓存管理器
    - L1缓存：cachetools内存缓存（主要）
    - L2缓存：选择性文件备份（重要数据）
    - 智能管理：自动TTL过期
    """

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self.config = load_config()
        self.cache_config = getattr(self.config, "cache", {})

        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)

        # 从配置加载TTL和内存限制
        self.cache_ttl = getattr(
            self.cache_config,
            "ttl",
            {
                "calendar": 14400,
                "subject": 7200,
                "episodes": 3600,
                "default": 1800,
            },
        )

        self.memory_limits = getattr(
            self.cache_config,
            "memory_limits",
            {
                "calendar": 10,
                "subject": 1000,
                "episodes": 500,
                "default": 100,
            },
        )

        self.persist_types = getattr(
            self.cache_config, "persist_types", ["calendar", "subject", "episodes"]
        )
        self.cleanup_on_startup = getattr(self.cache_config, "cleanup_on_startup", True)

        # 初始化cachetools缓存池
        self.memory_caches: Dict[str, TTLCache] = {}
        self.lock = threading.RLock()

        self._init_caches()

        # 启动时清理
        if self.cleanup_on_startup:
            self._cleanup_expired_files()

    def _init_caches(self) -> None:
        """初始化各类型的缓存池"""
        for cache_type in ["calendar", "subject", "episodes", "default"]:
            ttl = self.cache_ttl.get(cache_type, self.cache_ttl["default"])
            maxsize = self.memory_limits.get(cache_type, self.memory_limits["default"])

            self.memory_caches[cache_type] = TTLCache(maxsize=maxsize, ttl=ttl)

    def _cleanup_expired_files(self) -> None:
        """清理启动时的过期文件"""
        try:
            if not os.path.exists(self.cache_dir):
                return

            current_time = time.time()
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith(".json"):
                    continue

                filepath = os.path.join(self.cache_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)

                    if "timestamp" not in cache_data or "cache_type" not in cache_data:
                        continue

                    cache_type = cache_data["cache_type"]
                    ttl = self.cache_ttl.get(cache_type, self.cache_ttl["default"])

                    if current_time - cache_data["timestamp"] > ttl:
                        os.remove(filepath)
                        print(f"🗑️ 清理过期缓存文件: {filename}")

                except Exception:
                    # 删除损坏的文件
                    try:
                        os.remove(filepath)
                        print(f"🗑️ 清理损坏缓存文件: {filename}")
                    except Exception:
                        pass

        except Exception as e:
            print(f"清理缓存文件时出错: {e}")

    def _get_cache_file(self, key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{key}.json")

    def _should_persist(self, cache_type: str) -> bool:
        """判断是否需要持久化"""
        return cache_type in self.persist_types

    def _load_from_file(self, key: str, cache_type: str) -> Optional[Any]:
        """从文件加载缓存数据"""
        if not self._should_persist(cache_type):
            return None

        cache_file = self._get_cache_file(key)
        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # 检查文件缓存是否过期
            if "timestamp" not in cache_data:
                return None

            ttl = self.cache_ttl.get(cache_type, self.cache_ttl["default"])
            if time.time() - cache_data["timestamp"] > ttl:
                # 文件缓存过期，删除
                os.remove(cache_file)
                return None

            return cache_data.get("data")

        except Exception as e:
            print(f"读取缓存文件失败 {cache_file}: {e}")
            try:
                os.remove(cache_file)
            except Exception:
                pass
            return None

    def _save_to_file(self, key: str, data: Any, cache_type: str) -> None:
        """保存数据到文件"""
        if not self._should_persist(cache_type):
            return

        cache_file = self._get_cache_file(key)
        cache_data = {"data": data, "timestamp": time.time(), "cache_type": cache_type}

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入缓存文件失败 {cache_file}: {e}")

    def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """
        获取缓存数据
        优先从内存缓存获取，其次文件缓存
        """
        with self.lock:
            # 1. 尝试从内存缓存获取
            cache = self.memory_caches.get(cache_type, self.memory_caches["default"])

            if key in cache:
                return cache[key]

            # 2. 尝试从文件缓存加载
            file_data = self._load_from_file(key, cache_type)
            if file_data is not None:
                # 加载到内存缓存
                cache[key] = file_data
                return file_data

            return None

    def set(self, key: str, data: Any, cache_type: str = "default") -> None:
        """
        设置缓存数据
        同时写入内存和文件（如果需要持久化）
        """
        with self.lock:
            # 1. 写入内存缓存
            cache = self.memory_caches.get(cache_type, self.memory_caches["default"])
            cache[key] = data

            # 2. 写入文件缓存（如果需要持久化）
            self._save_to_file(key, data, cache_type)

    def clear(self, key: Optional[str] = None) -> None:
        """
        清理缓存
        如果指定key则只清理特定缓存，否则清理全部
        """
        with self.lock:
            if key:
                # 清理特定缓存
                for cache in self.memory_caches.values():
                    cache.pop(key, None)

                # 清理文件缓存
                cache_file = self._get_cache_file(key)
                if os.path.exists(cache_file):
                    try:
                        os.remove(cache_file)
                    except Exception as e:
                        print(f"删除缓存文件失败 {cache_file}: {e}")
            else:
                # 清理全部缓存
                for cache in self.memory_caches.values():
                    cache.clear()

                # 清理文件缓存
                try:
                    for filename in os.listdir(self.cache_dir):
                        if filename.endswith(".json"):
                            os.remove(os.path.join(self.cache_dir, filename))
                except Exception as e:
                    print(f"清理缓存目录失败: {e}")

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            memory_stats = {}
            total_memory_count = 0

            for cache_type, cache in self.memory_caches.items():
                count = len(cache)
                memory_stats[cache_type] = {
                    "count": count,
                    "maxsize": cache.maxsize,
                    "ttl": cache.ttl,
                }
                total_memory_count += count

            file_count = 0
            try:
                file_count = len([f for f in os.listdir(self.cache_dir) if f.endswith(".json")])
            except Exception:
                pass

            return {
                "memory_cache_stats": memory_stats,
                "total_memory_count": total_memory_count,
                "file_cache_count": file_count,
                "cache_config": {
                    "ttl": self.cache_ttl,
                    "memory_limits": self.memory_limits,
                    "persist_types": self.persist_types,
                },
            }
