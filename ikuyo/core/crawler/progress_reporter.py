#!/usr/bin/env python3
"""
进度汇报器
支持实时更新任务进度到数据库
"""

import logging
import json
from typing import Dict, Any, Optional
from ikuyo.core.redis_client import get_redis_connection


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
        self.logger.setLevel(logging.DEBUG) # Ensure debug messages are shown

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
            redis_client = get_redis_connection()
            channel = f"crawler_progress:{self.task_id}"
            message = json.dumps(progress_data)
            redis_client.publish(channel, message)
            self.logger.debug(f"任务 {self.task_id} 进度已发布到 Redis: {progress_data}")
            return True

        except Exception as e:
            self.logger.error(f"发布任务 {self.task_id} 进度到 Redis 时出错: {str(e)}")
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
            redis_client = get_redis_connection()
            channel = f"crawler_status:{self.task_id}"
            message_data = {"status": status, "error_message": error_message}
            redis_client.publish(channel, json.dumps(message_data))
            self.logger.info(f"任务 {self.task_id} 状态已发布到 Redis: {status}")
            return True

        except Exception as e:
            self.logger.error(f"发布任务 {self.task_id} 状态到 Redis 失败: {e}")
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
            redis_client = get_redis_connection()
            channel = f"crawler_result:{self.task_id}"
            message_data = {"result_summary": result_summary}
            redis_client.publish(channel, json.dumps(message_data))
            self.logger.info(f"任务 {self.task_id} 结果已发布到 Redis")
            return True

        except Exception as e:
            self.logger.error(f"发布任务 {self.task_id} 结果到 Redis 失败: {e}")
            return False
