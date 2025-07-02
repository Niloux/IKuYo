#!/usr/bin/env python3
"""
定时任务调度器（微服务解耦版）
只负责定时将定时任务写入crawler_tasks表，由worker服务消费。
"""

import logging
from typing import Any, Dict, List, Optional
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from ikuyo.core.repositories.scheduled_job_repository import ScheduledJobRepository
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.tasks.task_factory import TaskFactory
from ikuyo.core.database import get_session
import asyncio


class UnifiedScheduler:
    """
    统一任务调度器：所有定时任务通过数据库(scheduled_jobs表)驱动，统一调度和管理。
    只负责定时写入crawler_tasks表，由worker服务消费。
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler: Optional[BackgroundScheduler] = None
        self.is_running = False

    def init_scheduler(self) -> bool:
        try:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_listener(
                self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
            )
            self.logger.info("调度器初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"调度器初始化失败: {e}")
            return False

    def load_jobs_from_db(self):
        if not self.scheduler:
            self.logger.error("调度器未初始化")
            return
        with get_session() as session:
            job_repo = ScheduledJobRepository(session)
            jobs = job_repo.list()
            for job in jobs:
                if not job.enabled:
                    continue
                cron_expr = job.cron_expression
                cron_parts = cron_expr.split()
                if len(cron_parts) != 5:
                    self.logger.error(f"无效的cron表达式: {cron_expr}")
                    continue
                minute, hour, day, month, day_of_week = cron_parts
                self.scheduler.add_job(
                    func=self._write_scheduled_task,
                    trigger=CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week,
                    ),
                    id=job.job_id,
                    name=job.name,
                    args=[job],
                    replace_existing=True,
                )
                self.logger.info(
                    f"添加定时任务: {job.name} (ID: {job.job_id}, Cron: {cron_expr})"
                )

    def start(self) -> bool:
        if not self.scheduler:
            if not self.init_scheduler():
                return False
        if not self.scheduler:
            self.logger.error("调度器未初始化，无法启动")
            return False
        try:
            self.load_jobs_from_db()
            self.scheduler.start()
            self.is_running = True
            self.logger.info("统一任务调度器已启动")
            return True
        except Exception as e:
            self.logger.error(f"启动调度器失败: {e}")
            return False

    def stop(self) -> bool:
        if self.scheduler and self.is_running:
            try:
                self.scheduler.shutdown(wait=True)
                self.is_running = False
                self.logger.info("统一任务调度器已停止")
                return True
            except Exception as e:
                self.logger.error(f"停止调度器失败: {e}")
                return False
        return True

    def reload_jobs(self):
        if not self.scheduler:
            self.logger.error("调度器未初始化")
            return
        self.scheduler.remove_all_jobs()
        self.load_jobs_from_db()
        self.logger.info("定时任务已重新加载")

    def _write_scheduled_task(self, job):
        # 只写入任务表，状态设为pending，由worker消费
        with get_session() as session:
            task_repo = CrawlerTaskRepository(session)
            try:
                task = TaskFactory.create_task(
                    task_type="crawler",
                    parameters=job.parameters,
                    repository=task_repo,
                    spider_runner=None,
                    task_type_db="scheduled",
                )
                # 只需execute写入任务表
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(task.execute())
                else:
                    loop.run_until_complete(task.execute())
                self.logger.info(f"定时任务已写入任务表: {job.name}")
            except Exception as e:
                self.logger.error(f"定时任务写入异常: {e}")

    def _job_listener(self, event) -> None:
        if event.exception:
            self.logger.error(f"任务写入失败: {event.job_id} - {event.exception}")
        else:
            self.logger.info(f"任务写入成功: {event.job_id}")

    def get_jobs(self) -> List[Dict[str, Any]]:
        if not self.scheduler:
            return []
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time,
                    "trigger": str(job.trigger),
                }
            )
        return jobs
