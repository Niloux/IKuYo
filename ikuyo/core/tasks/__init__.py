"""
任务抽象和执行模块
"""

from .base import Task
from .crawler_task import CrawlerTask, CrawlerTaskParams
from .task_factory import TaskFactory

__all__ = [
    "Task",
    "CrawlerTask",
    "CrawlerTaskParams",
    "TaskFactory",
]
