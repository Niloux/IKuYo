import json
import logging
import os
import signal
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ValidationError

from ikuyo.core.models.crawler_task import CrawlerTask as CrawlerTaskModel
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.tasks.base import Task


class CrawlerTaskParams(BaseModel):
    mode: Literal["homepage", "season", "year"]
    year: Optional[int] = None
    season: Optional[Literal["春", "夏", "秋", "冬"]] = None
    limit: Optional[int] = None


class CrawlerTask(Task):
    """
    爬虫任务实现类，负责参数校验、执行、状态管理、异常处理等。
    采用同步实现，职责仅限于任务的创建和状态管理。
    """

    def __init__(
        self,
        repository: CrawlerTaskRepository,
        task_record=None,
        parameters=None,
        task_type_db="manual",
    ):
        super().__init__(repository, task_record)
        self.parameters = parameters  # 原始参数
        self.task_type_db = task_type_db
        self.params: Optional[CrawlerTaskParams] = None  # 结构化参数对象
        self.task_id: Optional[int] = task_record.id if task_record else None
        self.logger = logging.getLogger(f"crawler-task-{self.task_id or 'new'}")

    def validate(self) -> None:
        # 使用Pydantic模型进行参数校验
        params = (
            self.parameters
            if self.parameters
            else self.task_record.parameters
            if self.task_record
            else None
        )
        if not params:
            raise ValueError("爬虫任务参数不能为空")
        try:
            if isinstance(params, str):
                params = json.loads(params)
            self.params = CrawlerTaskParams(**params)
        except (ValidationError, Exception) as e:
            raise ValueError(f"爬虫任务参数校验失败: {e}")

    def write_to_db(self) -> None:
        """写入任务到数据库"""
        try:
            # 首先验证参数
            self.validate()

            # 准备任务参数
            if isinstance(self.parameters, dict):
                param_str = json.dumps(self.parameters)
            else:
                param_str = self.parameters or "{}"

            if not self.task_record:
                # 创建新任务记录
                self.task_record = CrawlerTaskModel(
                    task_type=self.task_type_db,
                    status="pending",
                    parameters=param_str,
                )
                self.repository.create(self.task_record)
                self.task_id = self.task_record.id
                self.logger = logging.getLogger(f"crawler-task-{self.task_id}")
            else:
                # 更新现有任务记录
                self.task_record.status = "pending"
                self.repository.update(self.task_record)

            self.logger.info(f"任务 {self.task_id} 已写入数据库，等待worker处理")

        except Exception as e:
            self.logger.error(f"写入任务到数据库失败: {e}")
            if self.task_record:
                # 更新任务状态为失败
                self.task_record.status = "failed"
                self.task_record.error_message = str(e)
                self.task_record.completed_at = self._now()
                self.repository.update(self.task_record)
            raise

    def execute(self) -> None:
        """
        执行爬虫任务（由worker调用）
        注意：此方法应该由worker服务在独立进程中调用
        """
        try:
            # 首先验证参数
            self.validate()

            if not self.task_id:
                raise ValueError("任务ID不存在")

            self.logger.info(f"开始执行爬虫任务 {self.task_id}")

            # 准备任务参数
            parameters = {}
            if isinstance(self.task_record.parameters, str):
                parameters = json.loads(self.task_record.parameters)
            elif self.task_record.parameters:
                parameters = self.task_record.parameters

            # 执行爬虫任务
            from ikuyo.core.crawler.spider_runner import SpiderRunner

            result = SpiderRunner.execute_in_process({
                "task_id": self.task_id,
                "task_type": "crawler",
                "parameters": parameters,
            })

            # 处理执行结果
            if result.get("status") == "completed":
                self.logger.info(f"任务 {self.task_id} 执行成功")
                self.task_record.status = "completed"
                if result.get("result"):
                    self.task_record.result = str(result["result"])
            else:
                error_msg = result.get("error", "未知错误")
                self.logger.error(f"任务 {self.task_id} 执行失败: {error_msg}")
                self.task_record.status = "failed"
                self.task_record.error_message = error_msg

            self.task_record.completed_at = self._now()
            self.repository.update(self.task_record)

        except Exception as e:
            self.logger.error(f"执行任务 {self.task_id} 失败: {e}")
            # 更新任务状态为失败
            self.task_record.status = "failed"
            self.task_record.error_message = str(e)
            self.task_record.completed_at = self._now()
            self.repository.update(self.task_record)
            raise

    def cancel(self) -> None:
        """取消爬虫任务"""
        try:
            if self.task_record.status in ["completed", "failed", "cancelled"]:
                self.logger.info(f"任务 {self.task_id} 已处于终结状态，无需取消。")
                return

            self.task_record.status = "cancelled"
            self.task_record.completed_at = self._now()
            self.task_record.error_message = "任务被用户取消"
            self.repository.update(self.task_record)
            self.logger.info(f"任务 {self.task_id} 状态已更新为 'cancelled'。")

            # 尝试发送信号给运行爬虫的进程
            if self.task_record.worker_pid:
                try:
                    os.kill(self.task_record.worker_pid, signal.SIGTERM)
                    self.logger.info(
                        f"已向 worker 进程 {self.task_record.worker_pid} 发送 SIGTERM 信号。"
                    )
                except ProcessLookupError:
                    self.logger.warning(
                        f"worker 进程 {self.task_record.worker_pid} 不存在，可能已退出。"
                    )
                except Exception as e:
                    self.logger.error(
                        f"发送信号给 worker 进程 {self.task_record.worker_pid} 失败: {e}"
                    )
            else:
                self.logger.warning(
                    f"任务 {self.task_id} 没有关联的 worker PID，无法发送取消信号。"
                )

        except Exception as e:
            self.logger.error(f"取消任务 {self.task_id} 失败: {e}")
            raise

    def _now(self):
        return datetime.now(timezone.utc)
