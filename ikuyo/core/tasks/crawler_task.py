from typing import Any, Dict, Optional
import json
from ikuyo.core.tasks.base import Task
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
import traceback
from pydantic import BaseModel, ValidationError
from ikuyo.core.config import load_config


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
        self.spider_runner = spider_runner  # 注入爬虫执行器（如CrawlerRunner实例）
        self.params: Optional[CrawlerTaskParams] = None  # 结构化参数对象

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
        self.on_status_change("running")
        self.task_record.status = "running"
        self.repository.update(self.task_record)
        try:
            # 确保参数已校验
            if self.params is None:
                self.validate()
            # 动态加载 config
            config = load_config()
            # 启动爬虫
            result = (
                await self.spider_runner.run(
                    config,
                    **self.params.model_dump(),
                    progress_callback=self.on_progress
                )
                if self.params
                else None
            )
            self.task_record.status = "completed"
            self.task_record.result_summary = json.dumps(result) if result else None
            self.task_record.completed_at = self._now()
            self.repository.update(self.task_record)
            self.on_status_change("completed")
        except Exception as e:
            self.task_record.status = "failed"
            self.task_record.error_message = f"{e}\n{traceback.format_exc()}"
            self.task_record.completed_at = self._now()
            self.repository.update(self.task_record)
            self.on_status_change("failed")

    async def cancel(self) -> None:
        # 取消任务的具体实现依赖于spider_runner的支持
        # 这里只做状态流转和记录
        self.task_record.status = "cancelled"
        self.task_record.completed_at = self._now()
        self.repository.update(self.task_record)
        self.on_status_change("cancelled")

    def on_progress(self, progress: Dict[str, Any]) -> None:
        # 可扩展为写入进度到数据库或推送到前端
        pass

    def on_status_change(self, status: str) -> None:
        # 可扩展为事件通知、日志等
        pass

    def _now(self):
        import datetime

        return datetime.datetime.now(datetime.timezone.utc)
