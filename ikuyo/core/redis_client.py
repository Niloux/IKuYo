#!/usr/bin/env python3
"""
Redis 客户端和连接池管理
"""

import redis
import logging
from typing import Optional


class RedisManager:
    """
    Redis 连接管理器 (单例)
    """

    _instance: Optional["RedisManager"] = None
    _connection_pool: Optional[redis.ConnectionPool] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ):
        if self._connection_pool is None:
            try:
                self.host = host
                self.port = port
                self.db = db
                self.password = password

                self._connection_pool = redis.ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,  # 自动将响应从 bytes 解码为 str
                )
                logging.info(
                    f"Redis connection pool created for {self.host}:{self.port}"
                )
            except Exception as e:
                logging.error(f"Failed to create Redis connection pool: {e}")
                raise

    def get_connection(self) -> redis.Redis:
        """
        从连接池获取一个 Redis 连接
        """
        if self._connection_pool is None:
            raise ConnectionError("Redis connection pool is not initialized.")
        return redis.Redis(connection_pool=self._connection_pool)

    def close_pool(self):
        """
        关闭连接池
        """
        if self._connection_pool:
            self._connection_pool.disconnect()
            self._connection_pool = None
            logging.info("Redis connection pool closed.")


# 全局实例
# 在实际使用中，可以通过一个函数来获取和初始化
_redis_manager: Optional[RedisManager] = None


def get_redis_manager() -> RedisManager:
    """
    获取全局 RedisManager 实例
    """
    global _redis_manager
    if _redis_manager is None:
        # 硬编码配置，后续可以从 config.yaml 读取
        _redis_manager = RedisManager(host="localhost", port=6379, db=0, password=None)
    return _redis_manager


def get_redis_connection() -> redis.Redis:
    """
    获取一个 Redis 连接
    """
    return get_redis_manager().get_connection()
