from abc import ABC, abstractmethod
from typing import Any, Dict


class Task(ABC):
    """
    任务抽象基类，定义统一的生命周期接口和核心属性。
    """

    def __init__(self, repository, task_record):
        self.repository = repository  # 任务Repository
        self.task_record = task_record  # 当前任务的数据库记录

    @abstractmethod
    def validate(self) -> None:
        """参数校验"""
        pass

    @abstractmethod
    async def execute(self) -> None:
        """异步执行主流程"""
        pass

    @abstractmethod
    async def cancel(self) -> None:
        """异步取消任务"""
        pass

    def on_progress(self, progress: Dict[str, Any]) -> None:
        """进度回调，可重写"""
        pass

    def on_status_change(self, status: str) -> None:
        """状态变更回调，可重写"""
        pass
