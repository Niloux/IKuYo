#!/usr/bin/env python3
"""
主工作器管理器
集成进程池和任务分发器，提供统一的worker管理接口
"""

import time
import signal
import logging
from typing import Optional
from ikuyo.core.worker.process_pool import ProcessPool
from ikuyo.core.worker.task_dispatcher import TaskDispatcher
from ikuyo.core.tasks.task_executor import set_process_pool


class WorkerManager:
    """
    工作器管理器
    统一管理进程池和任务分发器
    """

    def __init__(self, max_workers: int = 3, poll_interval: int = 2):
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.process_pool: Optional[ProcessPool] = None
        self.task_dispatcher: Optional[TaskDispatcher] = None
        self.is_running = False
        self.logger = logging.getLogger(__name__)

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def start(self) -> bool:
        """启动工作器"""
        try:
            if self.is_running:
                self.logger.warning("工作器已在运行中")
                return True

            self.logger.info("正在启动工作器...")

            # 设置日志
            self._setup_logging()

            # 创建并启动进程池
            self.process_pool = ProcessPool(max_workers=self.max_workers)
            if not self.process_pool.start():
                self.logger.error("进程池启动失败")
                return False

            # 注册进程池到TaskExecutor，使API可以使用进程池
            set_process_pool(self.process_pool)

            # 创建并启动任务分发器
            self.task_dispatcher = TaskDispatcher(
                process_pool=self.process_pool, poll_interval=self.poll_interval
            )
            if not self.task_dispatcher.start():
                self.logger.error("任务分发器启动失败")
                self.process_pool.stop()
                return False

            self.is_running = True
            self.logger.info(f"工作器启动成功，工作进程数: {self.max_workers}")

            return True

        except Exception as e:
            self.logger.error(f"启动工作器失败: {e}")
            return False

    def stop(self) -> bool:
        """停止工作器"""
        try:
            if not self.is_running:
                self.logger.info("工作器未在运行")
                return True

            self.logger.info("正在停止工作器...")
            self.is_running = False

            # 停止任务分发器
            if self.task_dispatcher:
                self.task_dispatcher.stop()

            # 停止进程池
            if self.process_pool:
                self.process_pool.stop()

            self.logger.info("工作器已停止")
            return True

        except Exception as e:
            self.logger.error(f"停止工作器失败: {e}")
            return False

    def run(self):
        """运行工作器主循环"""
        if not self.start():
            return

        try:
            self.logger.info("工作器主循环已启动，按 Ctrl+C 停止")

            while self.is_running:
                # 监控进程健康状态
                if self.process_pool:
                    self.process_pool.monitor_processes()

                # 打印状态信息
                self._log_status()

                time.sleep(10)  # 每10秒检查一次

        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号")
        except Exception as e:
            self.logger.error(f"工作器主循环异常: {e}")
            import traceback

            self.logger.error(f"异常详情: {traceback.format_exc()}")
        finally:
            self.stop()

    def get_status(self) -> dict:
        """获取工作器状态"""
        status = {
            "is_running": self.is_running,
            "max_workers": self.max_workers,
            "poll_interval": self.poll_interval,
        }

        if self.process_pool:
            status["process_pool"] = self.process_pool.get_pool_status()

        if self.task_dispatcher:
            status["task_dispatcher"] = self.task_dispatcher.get_dispatcher_status()

        return status

    def _setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("worker.log", encoding="utf-8"),
            ],
        )

    def _log_status(self):
        """记录状态信息"""
        try:
            if not self.process_pool or not self.task_dispatcher:
                return

            pool_status = self.process_pool.get_pool_status()
            dispatcher_status = self.task_dispatcher.get_dispatcher_status()

            self.logger.info(
                f"状态检查 - 总进程: {pool_status['total_workers']}, "
                f"空闲: {pool_status['idle_workers']}, "
                f"忙碌: {pool_status['busy_workers']}, "
                f"分发器运行: {dispatcher_status['is_running']}"
            )
        except Exception as e:
            self.logger.error(f"状态检查失败: {e}")

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在停止工作器...")
        self.is_running = False


def main():
    """主函数，兼容原worker.py的启动方式"""
    worker_manager = WorkerManager(max_workers=3, poll_interval=2)
    worker_manager.run()


if __name__ == "__main__":
    main()
