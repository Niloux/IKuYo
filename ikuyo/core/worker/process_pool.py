#!/usr/bin/env python3
"""
进程池管理器
管理多个工作进程，支持任务分发和负载均衡
"""

import multiprocessing as mp
import queue
import time
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ProcessStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class ProcessInfo:
    process: mp.Process
    status: ProcessStatus
    current_task_id: Optional[int] = None
    start_time: Optional[float] = None
    last_heartbeat: Optional[float] = None


class ProcessPool:
    """
    进程池管理器
    支持动态管理工作进程，任务分发和状态监控
    """

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.processes: Dict[int, ProcessInfo] = {}
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.control_queue = mp.Queue()
        self.is_running = False
        self.logger = logging.getLogger(__name__)

    def start(self) -> bool:
        """启动进程池"""
        try:
            self.is_running = True
            for i in range(self.max_workers):
                self._start_worker_process(i)
            self.logger.info(f"进程池启动成功，工作进程数: {self.max_workers}")
            return True
        except Exception as e:
            self.logger.error(f"进程池启动失败: {e}")
            return False

    def stop(self) -> bool:
        """停止进程池"""
        try:
            self.is_running = False
            # 发送停止信号
            for _ in range(self.max_workers):
                self.control_queue.put({"action": "stop"})

            # 等待进程结束
            for process_info in self.processes.values():
                if process_info.process.is_alive():
                    process_info.process.join(timeout=5)
                    if process_info.process.is_alive():
                        process_info.process.terminate()

            self.processes.clear()
            self.logger.info("进程池已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止进程池失败: {e}")
            return False

    def submit_task(self, task_data: Dict[str, Any]) -> bool:
        """提交任务到进程池"""
        try:
            if not self.is_running:
                return False

            self.task_queue.put(task_data, timeout=1)
            self.logger.info(f"任务已提交到进程池: task_id={task_data.get('task_id')}")
            return True
        except queue.Full:
            self.logger.warning("任务队列已满，提交失败")
            return False
        except Exception as e:
            self.logger.error(f"提交任务失败: {e}")
            return False

    def get_idle_workers(self) -> int:
        """获取空闲工作进程数量"""
        return sum(1 for info in self.processes.values() if info.status == ProcessStatus.IDLE)

    def get_busy_workers(self) -> int:
        """获取忙碌工作进程数量"""
        return sum(1 for info in self.processes.values() if info.status == ProcessStatus.BUSY)

    def get_pool_status(self) -> Dict[str, Any]:
        """获取进程池状态"""
        try:
            queue_size = self.task_queue.qsize() if hasattr(self.task_queue, "qsize") else 0
        except (OSError, NotImplementedError):
            # 某些平台可能不支持qsize()
            queue_size = 0

        return {
            "total_workers": len(self.processes),
            "idle_workers": self.get_idle_workers(),
            "busy_workers": self.get_busy_workers(),
            "is_running": self.is_running,
            "queue_size": queue_size,
        }

    def monitor_processes(self):
        """监控进程健康状态"""
        # current_time = time.time()
        for worker_id, process_info in list(self.processes.items()):
            if not process_info.process.is_alive():
                self.logger.warning(f"工作进程 {worker_id} 已停止，正在重启")
                self._restart_worker_process(worker_id)

    def _start_worker_process(self, worker_id: int):
        """启动单个工作进程"""
        try:
            process = mp.Process(
                target=self._worker_process,
                args=(worker_id, self.task_queue, self.result_queue, self.control_queue),
            )
            process.start()

            self.processes[worker_id] = ProcessInfo(
                process=process, status=ProcessStatus.IDLE, start_time=time.time()
            )
            self.logger.info(f"工作进程 {worker_id} 已启动，PID: {process.pid}")
        except Exception as e:
            self.logger.error(f"启动工作进程 {worker_id} 失败: {e}")

    def _restart_worker_process(self, worker_id: int):
        """重启工作进程"""
        if worker_id in self.processes:
            old_process = self.processes[worker_id].process
            if old_process.is_alive():
                old_process.terminate()
            del self.processes[worker_id]

        self._start_worker_process(worker_id)

    @staticmethod
    def _worker_process(
        worker_id: int, task_queue: mp.Queue, result_queue: mp.Queue, control_queue: mp.Queue
    ):
        """工作进程主函数"""
        logger = logging.getLogger(f"worker-{worker_id}")
        logger.info(f"工作进程 {worker_id} 已启动")

        while True:
            try:
                # 检查控制信号
                try:
                    control_msg = control_queue.get_nowait()
                    if control_msg.get("action") == "stop":
                        logger.info(f"工作进程 {worker_id} 收到停止信号")
                        break
                except queue.Empty:
                    pass

                # 获取任务
                try:
                    task_data = task_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # 执行任务
                task_id = task_data.get("task_id")
                logger.info(f"工作进程 {worker_id} 开始执行任务 {task_id}")

                # 调用SpiderRunner执行具体爬虫
                try:
                    from ikuyo.core.crawler.spider_runner import SpiderRunner

                    spider_result = SpiderRunner.execute_in_process(task_data)

                    result = {
                        "worker_id": worker_id,
                        "task_id": task_id,
                        "status": spider_result.get("status", "failed"),
                        "result": spider_result.get("result"),
                        "error": spider_result.get("error"),
                    }
                except Exception as e:
                    logger.error(f"SpiderRunner执行异常: {e}")
                    result = {
                        "worker_id": worker_id,
                        "task_id": task_id,
                        "status": "failed",
                        "result": None,
                        "error": str(e),
                    }

                result_queue.put(result)
                logger.info(f"工作进程 {worker_id} 完成任务 {task_id}")

            except Exception as e:
                logger.error(f"工作进程 {worker_id} 执行异常: {e}")
                if "task_id" in locals():
                    error_result = {
                        "worker_id": worker_id,
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e),
                    }
                    result_queue.put(error_result)

        logger.info(f"工作进程 {worker_id} 已退出")
