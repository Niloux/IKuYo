from abc import ABC, abstractmethod
from typing import Any, Dict


class Task(ABC):
    """
    任务抽象基类，定义统一的生命周期接口和核心属性。
    采用同步接口，职责仅限于任务的创建和状态管理。
    """

    def __init__(self, repository, task_record):
        self.repository = repository  # 任务Repository
        self.task_record = task_record  # 当前任务的数据库记录

    @abstractmethod
    def validate(self) -> None:
        """参数校验"""
        pass

    def write_to_db(self) -> None:
        """写入任务到数据库"""
        # 默认实现：验证参数并更新状态为pending
        self.validate()
        if self.task_record and hasattr(self.task_record, 'status'):
            self.task_record.status = "pending"
            self.repository.update(self.task_record)

    @abstractmethod
    def execute(self) -> None:
        """
        执行任务
        注意：此方法由worker调用，用于实际执行任务
        """
        pass

    def cancel(self) -> None:
        """取消任务"""
        if self.task_record and hasattr(self.task_record, 'status'):
            self.task_record.status = "cancelled"
            self.repository.update(self.task_record)

    def on_progress(self, progress: Dict[str, Any]) -> None:
        """进度回调，可重写"""
        pass

    def on_status_change(self, status: str) -> None:
        """状态变更回调，可重写"""
        pass
