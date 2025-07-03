from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class CrawlerTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_type: str  # 'manual' 或 'scheduled'
    status: str  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    parameters: Optional[str] = Field(default=None)
    result_summary: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    worker_pid: Optional[int] = Field(default=None, index=True)  # 用于存储执行该任务的 worker 进程 PID  # noqa: E501

    # 进度相关字段
    percentage: Optional[float] = Field(default=None)  # 总体完成百分比 (0-100)
    processed_items: Optional[int] = Field(default=None)  # 已处理项目数
    total_items: Optional[int] = Field(default=None)  # 总项目数
    processing_speed: Optional[float] = Field(default=None)  # 处理速度（项/秒）
    estimated_remaining: Optional[float] = Field(default=None)  # 预估剩余时间（秒）

    def update_progress(
        self,
        percentage: Optional[float] = None,
        processed_items: Optional[int] = None,
        total_items: Optional[int] = None,
        processing_speed: Optional[float] = None,
        estimated_remaining: Optional[float] = None,
    ) -> None:
        """更新任务进度信息"""
        if percentage is not None:
            self.percentage = round(percentage, 2)
        if processed_items is not None:
            self.processed_items = processed_items
        if total_items is not None:
            self.total_items = total_items
        if processing_speed is not None:
            self.processing_speed = round(processing_speed, 2)
        if estimated_remaining is not None:
            self.estimated_remaining = round(estimated_remaining, 2)
