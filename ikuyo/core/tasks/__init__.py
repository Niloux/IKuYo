"""
任务抽象和执行模块
"""

from .base import Task
from .crawler_task import CrawlerTask, CrawlerTaskParams
from .task_factory import TaskFactory
from .task_executor import TaskExecutor, get_task_executor, set_process_pool

__all__ = [
    "Task",
    "CrawlerTask",
    "CrawlerTaskParams",
    "TaskFactory",
    "TaskExecutor",
    "get_task_executor",
    "set_process_pool"
]
