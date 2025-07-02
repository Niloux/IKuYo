#!/usr/bin/env python3
"""
任务分发器
负责从数据库获取pending任务，分发到进程池执行
"""

import time
import json
import logging
import threading
import queue
from typing import Optional, Dict, Any
from ikuyo.core.database import get_session
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.worker.process_pool import ProcessPool


class TaskDispatcher:
    """
    任务分发器
    轮询数据库中的pending任务，分发到进程池执行
    """

    def __init__(self, process_pool: ProcessPool, poll_interval: int = 2):
        self.process_pool = process_pool
        self.poll_interval = poll_interval
        self.is_running = False
        self.dispatcher_thread: Optional[threading.Thread] = None
        self.result_processor_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)

    def start(self) -> bool:
        """启动任务分发器"""
        try:
            if self.is_running:
                return True

            self.is_running = True

            # 启动任务分发线程
            self.dispatcher_thread = threading.Thread(
                target=self._dispatch_loop, daemon=True, name="TaskDispatcher"
            )
            self.dispatcher_thread.start()

            # 启动结果处理线程
            self.result_processor_thread = threading.Thread(
                target=self._result_processing_loop, daemon=True, name="ResultProcessor"
            )
            self.result_processor_thread.start()

            self.logger.info("任务分发器已启动")
            return True
        except Exception as e:
            self.logger.error(f"启动任务分发器失败: {e}")
            return False

    def stop(self) -> bool:
        """停止任务分发器"""
        try:
            self.is_running = False

            # 等待线程结束
            if self.dispatcher_thread and self.dispatcher_thread.is_alive():
                self.dispatcher_thread.join(timeout=5)

            if self.result_processor_thread and self.result_processor_thread.is_alive():
                self.result_processor_thread.join(timeout=5)

            self.logger.info("任务分发器已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止任务分发器失败: {e}")
            return False

    def _dispatch_loop(self):
        """任务分发主循环"""
        self.logger.info("任务分发循环已启动")

        while self.is_running:
            try:
                # 检查是否有空闲工作进程
                idle_workers = self.process_pool.get_idle_workers()
                if idle_workers == 0:
                    time.sleep(self.poll_interval)
                    continue

                # 获取pending任务
                try:
                    with get_session() as session:
                        repo = CrawlerTaskRepository(session)
                        pending_tasks = repo.list_by_status("pending", limit=10)

                        if len(pending_tasks) > 0:
                            self.logger.info(
                                f"检查到 {len(pending_tasks)} 个pending任务, {idle_workers} 个空闲进程"
                            )

                        for task in pending_tasks:
                            if not self.is_running:
                                break

                            # 检查是否还有空闲进程
                            if self.process_pool.get_idle_workers() == 0:
                                break

                            self.logger.info(f"开始处理任务 {task.id}")

                            # 准备任务数据
                            task_data = self._prepare_task_data(task)
                            if not task_data:
                                self.logger.warning(f"任务 {task.id} 数据准备失败，跳过")
                                continue

                            # 标记任务为running
                            try:
                                task.status = "running"
                                task.started_at = self._get_current_time()
                                repo.update(task)
                            except Exception as update_error:
                                self.logger.error(f"更新任务 {task.id} 状态失败: {update_error}")
                                continue

                            # 提交到进程池
                            if self.process_pool.submit_task(task_data):
                                self.logger.info(f"任务 {task.id} 已分发到进程池")
                            else:
                                # 提交失败，回滚状态
                                task.status = "pending"
                                task.started_at = None
                                repo.update(task)
                                self.logger.warning(f"任务 {task.id} 分发失败，已回滚状态")

                except Exception as db_error:
                    self.logger.error(f"数据库操作失败: {db_error}")
                    import traceback

                    self.logger.error(f"数据库异常详情: {traceback.format_exc()}")
                    time.sleep(self.poll_interval)
                    continue

            except Exception as e:
                self.logger.error(f"任务分发循环异常: {e}")

            time.sleep(self.poll_interval)

        self.logger.info("任务分发循环已退出")

    def _result_processing_loop(self):
        """结果处理主循环"""
        self.logger.info("结果处理循环已启动")

        while self.is_running:
            try:
                # 获取执行结果
                try:
                    result = self.process_pool.result_queue.get(timeout=1)
                    self._process_task_result(result)
                except queue.Empty:
                    # 队列为空，正常情况，继续循环
                    continue
                except Exception as queue_error:
                    # 其他队列错误
                    self.logger.error(f"队列操作异常: {queue_error}")
                    import traceback

                    self.logger.error(f"队列异常详情: {traceback.format_exc()}")
                    # 等待一下再继续，避免连续错误
                    time.sleep(1)
                    continue

            except Exception as e:
                self.logger.error(f"结果处理循环异常: {e}")
                import traceback

                self.logger.error(f"异常详情: {traceback.format_exc()}")
                break

        self.logger.info("结果处理循环已退出")

    def _prepare_task_data(self, task) -> Optional[Dict[str, Any]]:
        """准备任务数据"""
        try:
            # 解析任务参数
            params = task.parameters
            if isinstance(params, str):
                params = json.loads(params)

            if not params:
                self.logger.warning(f"任务 {task.id} 参数为空，跳过")
                return None

            task_data = {
                "task_id": task.id,
                "task_type": task.task_type,
                "parameters": params,
                "created_at": task.created_at.isoformat() if task.created_at else None,
            }

            return task_data

        except Exception as e:
            self.logger.error(f"准备任务 {task.id} 数据失败: {e}")
            return None

    def _process_task_result(self, result: Dict[str, Any]):
        """处理任务执行结果"""
        try:
            task_id = result.get("task_id")
            status = result.get("status")
            worker_id = result.get("worker_id")

            if not task_id:
                self.logger.warning("收到无效的任务结果，缺少task_id")
                return

            with get_session() as session:
                repo = CrawlerTaskRepository(session)
                task = repo.get_by_id(task_id)

                if not task:
                    self.logger.warning(f"未找到任务 {task_id}，可能已被删除")
                    return

                # 更新任务状态
                if status == "completed":
                    task.status = "completed"
                    task.completed_at = self._get_current_time()
                    # 将结果转换为JSON字符串存储
                    result_data = result.get("result", "")
                    if isinstance(result_data, dict):
                        task.result_summary = json.dumps(result_data, ensure_ascii=False)
                    else:
                        task.result_summary = str(result_data)
                    self.logger.info(f"任务 {task_id} 在工作进程 {worker_id} 中执行完成")

                elif status == "failed":
                    task.status = "failed"
                    task.completed_at = self._get_current_time()
                    task.error_message = result.get("error", "未知错误")
                    self.logger.error(
                        f"任务 {task_id} 在工作进程 {worker_id} 中执行失败: {task.error_message}"
                    )

                else:
                    self.logger.warning(f"收到未知的任务状态: {status}")
                    return

                repo.update(task)

        except Exception as e:
            self.logger.error(f"处理任务结果失败: {e}")

    def get_dispatcher_status(self) -> Dict[str, Any]:
        """获取分发器状态"""
        return {
            "is_running": self.is_running,
            "poll_interval": self.poll_interval,
            "dispatcher_thread_alive": (
                self.dispatcher_thread.is_alive() if self.dispatcher_thread else False
            ),
            "result_processor_thread_alive": (
                self.result_processor_thread.is_alive() if self.result_processor_thread else False
            ),
            "process_pool_status": self.process_pool.get_pool_status(),
        }

    def _get_current_time(self):
        """获取当前时间"""
        import datetime

        return datetime.datetime.now(datetime.timezone.utc)
