#!/usr/bin/env python3
"""
进度汇报器
支持实时更新任务进度到数据库
"""

import logging
from typing import Dict, Any, Optional
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.database import get_session


class ProgressReporter:
    """爬虫进度报告器"""

    def __init__(self, task_id: int):
        """
        初始化进度报告器

        Args:
            task_id: 任务ID
        """
        self.task_id = task_id
        self.logger = logging.getLogger(f"progress-reporter-{task_id}")

    def report_progress(self, progress_data: Dict[str, Any]) -> bool:
        """
        报告进度

        Args:
            progress_data: 进度数据，包含以下字段：
                - percentage: 总体完成百分比 (0-100)
                - processed_items: 已处理项目数
                - total_items: 总项目数
                - processing_speed: 处理速度（项/秒）
                - estimated_remaining: 预估剩余时间（秒）

        Returns:
            bool: 是否成功更新进度
        """
        try:
            with get_session() as session:
                repo = CrawlerTaskRepository(session)
                task = repo.get_by_id(self.task_id)
                if not task:
                    self.logger.error(f"任务 {self.task_id} 不存在")
                    return False

                task.update_progress(
                    percentage=progress_data.get("percentage"),
                    processed_items=progress_data.get("processed_items"),
                    total_items=progress_data.get("total_items"),
                    processing_speed=progress_data.get("processing_speed"),
                    estimated_remaining=progress_data.get("estimated_remaining"),
                )

                repo.update(task)
                self.logger.debug(f"任务 {self.task_id} 进度已更新: {progress_data}")
                return True

        except Exception as e:
            self.logger.error(f"更新任务 {self.task_id} 进度时出错: {str(e)}")
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


# 全局进度报告器实例
_current_reporter: Optional[ProgressReporter] = None


def init_progress_reporter(task_id: int) -> None:
    """初始化全局进度报告器"""
    global _current_reporter
    _current_reporter = ProgressReporter(task_id)


def report_progress(progress_data: Dict[str, Any]) -> bool:
    """全局进度报告函数"""
    if not _current_reporter:
        return False
    return _current_reporter.report_progress(progress_data)


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
