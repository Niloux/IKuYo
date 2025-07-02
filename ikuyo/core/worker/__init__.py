"""
工作器核心模块
提供多进程并发执行爬虫任务的能力
"""

from .main import WorkerManager
from .process_pool import ProcessPool
from .redis_consumer import RedisTaskConsumer

__all__ = [
    "WorkerManager",
    "ProcessPool",
    "RedisTaskConsumer",
]
