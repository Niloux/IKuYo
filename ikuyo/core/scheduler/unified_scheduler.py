#!/usr/bin/env python3
"""
统一任务调度器
只负责定时将定时任务写入crawler_tasks表，由worker服务消费。
采用纯同步实现，移除异步复杂性。
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
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class UnifiedScheduler:
    """
    统一任务调度器：所有定时任务通过数据库(scheduled_jobs表)驱动，统一调度和管理。
    只负责定时写入crawler_tasks表，由worker服务消费。
    采用纯同步实现，避免异步复杂性。
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler: Optional[BackgroundScheduler] = None
        self.is_running = False

    def init_scheduler(self) -> bool:
        """初始化调度器"""
        try:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
            self.logger.info("调度器初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"调度器初始化失败: {e}")
            return False

    def load_jobs_from_db(self):
        """从数据库加载定时任务配置"""
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
                        minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
                    ),
                    id=job.job_id,
                    name=job.name,
                    args=[job],
                    replace_existing=True,
                )
                self.logger.info(f"添加定时任务: {job.name} (ID: {job.job_id}, Cron: {cron_expr})")

    def start(self) -> bool:
        """启动调度器"""
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
        """停止调度器"""
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
        """重新加载定时任务配置"""
        if not self.scheduler:
            self.logger.error("调度器未初始化")
            return
        self.scheduler.remove_all_jobs()
        self.load_jobs_from_db()
        self.logger.info("定时任务已重新加载")

    def _write_scheduled_task(self, job):
        """将定时任务写入任务表"""
        with get_session() as session:
            task_repo = CrawlerTaskRepository(session)
            try:
                # 解析JSON参数
                parameters = json.loads(job.parameters) if job.parameters else {}
                task = TaskFactory.create_task(
                    task_type="crawler",
                    parameters=parameters,
                    repository=task_repo,
                    task_type_db="scheduled",
                )
                # 使用同步方法写入任务
                task.write_to_db()
                self.logger.info(f"定时任务已写入任务表: {job.name}")
            except Exception as e:
                self.logger.error(f"定时任务写入异常: {e}")

    def _job_listener(self, event) -> None:
        """任务执行状态监听器"""
        if event.exception:
            self.logger.error(f"任务写入失败: {event.job_id} - {event.exception}")
        else:
            self.logger.info(f"任务写入成功: {event.job_id}")

    def get_jobs(self) -> List[Dict[str, Any]]:
        """获取所有定时任务状态"""
        if not self.scheduler:
            return []
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
            })
        return jobs
