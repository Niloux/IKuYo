from typing import Any, Dict, Optional
import json
import logging
from ikuyo.core.tasks.base import Task
from ikuyo.core.tasks.task_executor import get_task_executor
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

    def __init__(self, repository: CrawlerTaskRepository, task_record, spider_runner=None):
        super().__init__(repository, task_record)
        self.spider_runner = spider_runner  # 兼容旧接口，可移除
        self.params: Optional[CrawlerTaskParams] = None  # 结构化参数对象
        self.task_id: Optional[int] = task_record.id if task_record else None
        self.logger = logging.getLogger(f"crawler-task-{self.task_id}")

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
        """
        执行爬虫任务
        优先使用进程池执行，降级到当前进程执行
        """
        try:
            # 首先验证参数
            self.validate()

            if not self.task_id:
                raise ValueError("任务ID不存在")

            self.logger.info(f"开始执行爬虫任务 {self.task_id}")

            # 更新任务状态为pending（为了与API兼容）
            self.on_status_change("pending")
            self.task_record.status = "pending"
            self.repository.update(self.task_record)

            # 获取任务执行器并尝试提交到进程池
            executor = get_task_executor()

            # 准备任务参数
            parameters = {}
            if isinstance(self.task_record.parameters, str):
                parameters = json.loads(self.task_record.parameters)
            elif self.task_record.parameters:
                parameters = self.task_record.parameters

            # 尝试在进程池中执行
            success = await executor.execute_task(
                task_id=self.task_id, task_type="crawler", parameters=parameters
            )

            if success:
                self.logger.info(f"任务 {self.task_id} 已提交到进程池执行")
            else:
                self.logger.warning(
                    f"任务 {self.task_id} 未能提交到进程池，可能需要等待worker处理"
                )

        except Exception as e:
            self.logger.error(f"执行任务 {self.task_id} 失败: {e}")
            # 更新任务状态为失败
            self.task_record.status = "failed"
            self.task_record.error_message = str(e)
            self.task_record.completed_at = self._now()
            self.repository.update(self.task_record)
            raise

    async def cancel(self) -> None:
        """取消任务"""
        try:
            if self.task_id:
                self.logger.info(f"取消任务 {self.task_id}")
                self.task_record.status = "cancelled"
                self.task_record.completed_at = self._now()
                self.repository.update(self.task_record)
                self.on_status_change("cancelled")
            else:
                self.logger.warning("无法取消任务：任务ID不存在")
        except Exception as e:
            self.logger.error(f"取消任务 {self.task_id} 失败: {e}")

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
