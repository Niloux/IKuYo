#!/usr/bin/env python3
"""
任务执行协调器
集成进程池执行和现有任务抽象层，保持API兼容性
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from ikuyo.core.worker.process_pool import ProcessPool
from ikuyo.core.crawler.progress_reporter import ProgressReporter


class TaskExecutor:
    """
    任务执行协调器
    协调任务抽象层和进程池执行，保持API兼容性
    """

    _instance: Optional["TaskExecutor"] = None
    _process_pool: Optional[ProcessPool] = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @classmethod
    def get_instance(cls) -> "TaskExecutor":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_process_pool(cls, process_pool: ProcessPool):
        """设置进程池实例"""
        cls._process_pool = process_pool

    async def execute_task(self, task_id: int, task_type: str, parameters: Dict[str, Any]) -> bool:
        """
        执行任务
        Args:
            task_id: 任务ID
            task_type: 任务类型
            parameters: 任务参数
        Returns:
            bool: 是否成功提交到进程池
        """
        try:
            # 检查进程池是否可用
            if not self._process_pool or not self._process_pool.is_running:
                self.logger.warning("进程池未启动，任务将在当前进程中执行")
                return await self._execute_in_current_process(task_id, task_type, parameters)

            # 检查是否有空闲工作进程
            if self._process_pool.get_idle_workers() == 0:
                self.logger.warning("没有空闲工作进程，任务将等待分发")
                # 这里可以选择等待或返回False让TaskDispatcher处理
                return False

            # 准备任务数据
            task_data = {"task_id": task_id, "task_type": task_type, "parameters": parameters}

            # 提交到进程池
            success = self._process_pool.submit_task(task_data)
            if success:
                self.logger.info(f"任务 {task_id} 已提交到进程池")
            else:
                self.logger.warning(f"任务 {task_id} 提交到进程池失败")

            return success

        except Exception as e:
            self.logger.error(f"执行任务 {task_id} 失败: {e}")
            return False

    async def _execute_in_current_process(
        self, task_id: int, task_type: str, parameters: Dict[str, Any]
    ) -> bool:
        """
        在当前进程中执行任务（降级方案）
        """
        try:
            self.logger.info(f"在当前进程中执行任务 {task_id}")

            if task_type == "crawler":
                # 导入并执行爬虫任务
                from ikuyo.core.crawler.spider_runner import SpiderRunner

                task_data = {"task_id": task_id, "task_type": task_type, "parameters": parameters}

                # 在异步上下文中运行同步的爬虫代码
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, SpiderRunner.execute_in_process, task_data
                )

                # 更新任务状态
                reporter = ProgressReporter(task_id)
                if result.get("status") == "completed":
                    reporter.report_status("completed")
                    if result.get("result"):
                        reporter.report_result(str(result["result"]))
                else:
                    reporter.report_status("failed", result.get("error"))

                return result.get("status") == "completed"
            else:
                self.logger.error(f"不支持的任务类型: {task_type}")
                return False

        except Exception as e:
            self.logger.error(f"在当前进程中执行任务 {task_id} 失败: {e}")

            # 报告任务失败
            try:
                reporter = ProgressReporter(task_id)
                reporter.report_status("failed", str(e))
            except Exception:
                pass  # 忽略报告错误

            return False

    def get_execution_status(self) -> Dict[str, Any]:
        """获取执行器状态"""
        status = {
            "process_pool_available": self._process_pool is not None,
            "process_pool_running": (
                self._process_pool.is_running if self._process_pool else False
            ),
        }

        if self._process_pool:
            status.update(self._process_pool.get_pool_status())

        return status


# 全局执行器实例
def get_task_executor() -> TaskExecutor:
    """获取全局任务执行器实例"""
    return TaskExecutor.get_instance()


def set_process_pool(process_pool: ProcessPool):
    """设置全局进程池"""
    TaskExecutor.set_process_pool(process_pool)
