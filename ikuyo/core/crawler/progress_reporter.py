#!/usr/bin/env python3
"""
进度汇报器
支持实时更新任务进度到数据库
"""

import json
import logging
from typing import Dict, Any, Optional
from ikuyo.core.database import get_session
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository


class ProgressReporter:
    """
    进度汇报器
    负责将爬虫执行进度实时更新到数据库
    """

    def __init__(self, task_id: int):
        self.task_id = task_id
        self.logger = logging.getLogger(f"progress-reporter-{task_id}")

    def report_progress(self, progress_data: Dict[str, Any]) -> bool:
        """
        汇报任务进度

        Args:
            progress_data: 进度数据，包含percentage、current_item、total_items等

        Returns:
            bool: 是否汇报成功
        """
        try:
            with get_session() as session:
                repo = CrawlerTaskRepository(session)
                task = repo.get_by_id(self.task_id)

                if not task:
                    self.logger.warning(f"任务 {self.task_id} 不存在，无法更新进度")
                    return False

                # 序列化进度数据
                progress_json = json.dumps(progress_data, ensure_ascii=False)
                task.progress = progress_json
                repo.update(task)

                self.logger.debug(f"任务 {self.task_id} 进度已更新: {progress_data}")
                return True

        except Exception as e:
            self.logger.error(f"汇报任务 {self.task_id} 进度失败: {e}")
            return False

    def report_status(self, status: str, error_message: Optional[str] = None) -> bool:
        """
        汇报任务状态

        Args:
            status: 任务状态 (running, completed, failed, cancelled)
            error_message: 错误信息（可选）

        Returns:
            bool: 是否汇报成功
        """
        try:
            with get_session() as session:
                repo = CrawlerTaskRepository(session)
                task = repo.get_by_id(self.task_id)

                if not task:
                    self.logger.warning(f"任务 {self.task_id} 不存在，无法更新状态")
                    return False

                task.status = status
                if error_message:
                    task.error_message = error_message

                if status in ["completed", "failed", "cancelled"]:
                    task.completed_at = self._get_current_time()

                repo.update(task)

                self.logger.info(f"任务 {self.task_id} 状态已更新为: {status}")
                return True

        except Exception as e:
            self.logger.error(f"汇报任务 {self.task_id} 状态失败: {e}")
            return False

    def report_result(self, result_summary: str) -> bool:
        """
        汇报任务结果

        Args:
            result_summary: 结果摘要

        Returns:
            bool: 是否汇报成功
        """
        try:
            with get_session() as session:
                repo = CrawlerTaskRepository(session)
                task = repo.get_by_id(self.task_id)

                if not task:
                    self.logger.warning(f"任务 {self.task_id} 不存在，无法更新结果")
                    return False

                task.result_summary = result_summary
                repo.update(task)

                self.logger.info(f"任务 {self.task_id} 结果已更新")
                return True

        except Exception as e:
            self.logger.error(f"汇报任务 {self.task_id} 结果失败: {e}")
            return False

    def _get_current_time(self):
        """获取当前时间"""
        import datetime

        return datetime.datetime.now(datetime.timezone.utc)


# 全局进度汇报函数，便于在爬虫中使用
_current_reporter: Optional[ProgressReporter] = None


def set_current_task(task_id: int):
    """设置当前任务ID，用于全局进度汇报"""
    global _current_reporter
    _current_reporter = ProgressReporter(task_id)


def report_progress(progress_data: Dict[str, Any]) -> bool:
    """全局进度汇报函数"""
    if _current_reporter:
        return _current_reporter.report_progress(progress_data)
    return False


def report_status(status: str, error_message: Optional[str] = None) -> bool:
    """全局状态汇报函数"""
    if _current_reporter:
        return _current_reporter.report_status(status, error_message)
    return False


def report_result(result_summary: str) -> bool:
    """全局结果汇报函数"""
    if _current_reporter:
        return _current_reporter.report_result(result_summary)
    return False
