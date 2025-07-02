#!/usr/bin/env python3
"""
Redis 任务消费者
负责从 Redis 任务队列中获取任务，并分发到进程池执行
"""

import time
import json
import logging
import threading
from typing import Optional, Dict, Any

import redis.exceptions

from ikuyo.core.database import get_session
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.worker.process_pool import ProcessPool
from ikuyo.core.redis_client import get_redis_connection


class RedisTaskConsumer:
    """
    从 Redis 队列中消费任务并分发
    """

    def __init__(
        self, process_pool: ProcessPool, queue_name: str = "ikuyo:crawl_tasks"
    ):
        self.process_pool = process_pool
        self.queue_name = queue_name
        self.is_running = False
        self.consumer_thread: Optional[threading.Thread] = None
        self.redis_client: redis.Redis = get_redis_connection()
        self.logger = logging.getLogger(__name__)

    def start(self) -> bool:
        """
        启动任务消费者
        """
        try:
            if self.is_running:
                return True

            # 测试 Redis 连接
            self.redis_client.ping()
            self.logger.info("Redis connection successful.")

            self.is_running = True
            self.consumer_thread = threading.Thread(
                target=self._consume_loop, daemon=True, name="RedisTaskConsumer"
            )
            self.consumer_thread.start()
            self.logger.info(
                f"Task consumer started. Listening on queue: {self.queue_name}"
            )
            return True
        except redis.exceptions.ConnectionError as e:
            self.logger.error(
                f"Redis connection failed: {e}. The worker cannot start without Redis."
            )
            return False
        except Exception as e:
            self.logger.error(f"Failed to start task consumer: {e}")
            return False

    def stop(self) -> bool:
        """
        停止任务消费者
        """
        try:
            self.is_running = False
            if self.consumer_thread and self.consumer_thread.is_alive():
                self.consumer_thread.join(timeout=5)
            self.logger.info("Task consumer stopped.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop task consumer: {e}")
            return False

    def _consume_loop(self):
        """
        任务消费主循环
        """
        self.logger.info("Task consumption loop started.")
        while self.is_running:
            try:
                # 检查是否有空闲进程
                if self.process_pool.get_idle_workers() == 0:
                    time.sleep(1)  # 如果进程池满了，稍等一下再检查
                    continue

                # 使用 BRPOP 阻塞式地从 Redis 队列获取任务
                # timeout 设置为1秒，以便循环可以定期检查 is_running 状态
                message = self.redis_client.brpop([self.queue_name], timeout=1)
                if message is None:
                    continue

                if not isinstance(message, (list, tuple)) or len(message) != 2:
                    self.logger.warning(f"Received malformed message from Redis: {message}")
                    continue

                _queue, task_message = message
                try:
                    task_data = json.loads(task_message)
                except Exception as e:
                    self.logger.error(f"Failed to parse task message: {task_message}, error: {e}")
                    continue

                task_id = task_data.get("task_id")

                if not task_id:
                    self.logger.warning(
                        f"Received invalid message from Redis: {task_message}"
                    )
                    continue

                self.logger.info(f"Received task {task_id} from Redis queue.")
                self._process_task(task_id)

            except redis.exceptions.ConnectionError as e:
                self.logger.error(
                    f"Redis connection lost in consumer loop: {e}. Retrying in 5 seconds..."
                )
                time.sleep(5)
            except json.JSONDecodeError as e:
                self.logger.error(
                    f"Failed to decode task message: {e}. Message: {_queue}"
                )
            except Exception as e:
                self.logger.error(f"An error occurred in the consumer loop: {e}")
                time.sleep(1)

        self.logger.info("Task consumption loop has exited.")

    def _process_task(self, task_id: int):
        """
        从数据库获取任务详情并分发
        """
        try:
            with get_session() as session:
                repo = CrawlerTaskRepository(session)
                task = repo.get_by_id(task_id)

                if not task:
                    self.logger.warning(
                        f"Task {task_id} not found in database, skipping."
                    )
                    return

                if task.status != "pending":
                    self.logger.info(
                        f"Task {task_id} has status '{task.status}', not 'pending'. Skipping."
                    )
                    return

                # 准备任务数据
                task_data_for_process = self._prepare_task_data(task)
                if not task_data_for_process:
                    self.logger.error(
                        f"Failed to prepare data for task {task_id}. Aborting task."
                    )
                    # Consider marking the task as failed here
                    return

                # 更新任务状态为 'running'
                try:
                    task.status = "running"
                    task.started_at = self._get_current_time()
                    repo.update(task)
                except Exception as e:
                    self.logger.error(
                        f"Failed to update task {task_id} status to 'running': {e}"
                    )
                    return  # Do not proceed if status update fails

                # 提交到进程池
                if self.process_pool.submit_task(task_data_for_process):
                    self.logger.info(f"Task {task_id} dispatched to process pool.")
                else:
                    self.logger.warning(
                        f"Failed to dispatch task {task_id} to process pool. Rolling back status."
                    )
                    # 回滚状态
                    task.status = "pending"
                    task.started_at = None
                    repo.update(task)

        except Exception as e:
            self.logger.error(f"Failed to process task {task_id}: {e}")

    def _prepare_task_data(self, task) -> Optional[Dict[str, Any]]:
        """
        准备要传递给子进程的任务数据字典
        """
        try:
            params = task.parameters
            if isinstance(params, str):
                params = json.loads(params)

            return {
                "task_id": task.id,
                "task_type": task.task_type,
                "parameters": params,
                "created_at": task.created_at.isoformat() if task.created_at else None,
            }
        except Exception as e:
            self.logger.error(f"Failed to prepare task data for task {task.id}: {e}")
            return None

    def _get_current_time(self):
        import datetime

        return datetime.datetime.now(datetime.timezone.utc)
