from typing import Any, Dict, Optional
import json
from ikuyo.core.tasks.base import Task
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from pydantic import BaseModel, ValidationError


class CrawlerTaskParams(BaseModel):
    mode: str
    year: Optional[int] = None
    season: Optional[str] = None
    start_url: Optional[str] = None
    limit: Optional[int] = None
    # 待扩展


class CrawlerTask(Task):
    """
    爬虫任务实现类，负责参数校验、异步执行、状态管理、异常处理等。
    """

    def __init__(self, repository: CrawlerTaskRepository, task_record, spider_runner):
        super().__init__(repository, task_record)
        self.spider_runner = spider_runner  # 兼容旧接口，可移除
        self.params: Optional[CrawlerTaskParams] = None  # 结构化参数对象
        self.task_id: Optional[str] = None

    def validate(self) -> None:
        # 使用Pydantic模型进行参数校验
        params = self.task_record.parameters
        if not params:
            raise ValueError("爬虫任务参数不能为空")
        try:
            if isinstance(params, str):
                params = json.loads(params)
            self.params = CrawlerTaskParams(**params)
        except (ValidationError, Exception) as e:
            raise ValueError(f"爬虫任务参数校验失败: {e}")

    async def execute(self) -> None:
        self.on_status_change("pending")
        self.task_record.status = "pending"
        self.repository.update(self.task_record)

    async def cancel(self) -> None:
        if self.task_id:
            self.task_record.status = "cancelled"
            self.task_record.completed_at = self._now()
            self.repository.update(self.task_record)
            self.on_status_change("cancelled")

    def on_progress(self, progress: Dict[str, Any]) -> None:
        try:
            with open("./worker_debug.log", "a") as f:
                f.write(f"[DEBUG] on_progress called: {progress}\n")
            self.task_record.progress = json.dumps(progress)
            self.repository.update(self.task_record)
        except Exception:
            pass

    def on_status_change(self, status: str) -> None:
        # 可扩展为事件通知、日志等
        pass

    def _now(self):
        import datetime

        return datetime.datetime.now(datetime.timezone.utc)
