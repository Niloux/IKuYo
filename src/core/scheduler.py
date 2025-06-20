#!/usr/bin/env python3
"""
定时任务调度器
基于APScheduler实现定时爬虫任务
"""

import logging
from typing import Any, Dict, List, Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import load_config


class CrawlerScheduler:
    """爬虫定时任务调度器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler: Optional[BackgroundScheduler] = None
        self.is_running = False

        config = load_config()
        self.scheduler_config = getattr(config, "scheduler", {})

    def init_scheduler(self) -> bool:
        """初始化调度器"""
        try:
            # 获取调度器配置
            timezone = self.scheduler_config.get("timezone", "Asia/Shanghai")
            job_defaults = self.scheduler_config.get("scheduler_settings", {}).get(
                "job_defaults", {}
            )

            # 创建后台调度器
            self.scheduler = BackgroundScheduler(timezone=timezone, job_defaults=job_defaults)

            # 添加事件监听器
            if self.scheduler:
                self.scheduler.add_listener(
                    self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
                )

            self.logger.info("调度器初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"调度器初始化失败: {e}")
            return False

    def add_crawler_job(self) -> None:
        """添加爬虫定时任务"""
        if not self.scheduler:
            self.logger.error("调度器未初始化")
            return

        try:
            jobs = self.scheduler_config.get("jobs", [])

            for job_config in jobs:
                if not job_config.get("enabled", True):
                    continue

                job_id = job_config["id"]
                job_name = job_config["name"]
                cron_expr = job_config["cron"]
                description = job_config.get("description", "")

                # 解析cron表达式
                cron_parts = cron_expr.split()
                if len(cron_parts) != 5:
                    self.logger.error(f"无效的cron表达式: {cron_expr}")
                    continue

                minute, hour, day, month, day_of_week = cron_parts

                # 添加定时任务
                self.scheduler.add_job(
                    func=self._run_crawler,
                    trigger=CronTrigger(
                        minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
                    ),
                    id=job_id,
                    name=job_name,
                    description=description,
                    replace_existing=True,
                )

                self.logger.info(f"添加定时任务: {job_name} (ID: {job_id}, Cron: {cron_expr})")

        except Exception as e:
            self.logger.error(f"添加定时任务失败: {e}")

    def start(self) -> bool:
        """启动调度器"""
        if not self.scheduler:
            if not self.init_scheduler():
                return False

        try:
            # 添加爬虫任务
            self.add_crawler_job()

            # 启动调度器
            if self.scheduler:
                self.scheduler.start()
                self.is_running = True

            self.logger.info("定时任务调度器已启动")
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
                self.logger.info("定时任务调度器已停止")
                return True
            except Exception as e:
                self.logger.error(f"停止调度器失败: {e}")
                return False
        return True

    def get_jobs(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
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

    def _run_crawler(self) -> None:
        """执行爬虫任务"""
        try:
            self.logger.info("开始执行定时爬虫任务")

            # 导入并运行爬虫
            from scrapy.crawler import CrawlerProcess
            from scrapy.utils.project import get_project_settings

            # 获取项目设置
            settings = get_project_settings()

            # 创建爬虫进程
            process = CrawlerProcess(settings)
            process.crawl("mikan")
            process.start()

            self.logger.info("定时爬虫任务执行完成")

        except Exception as e:
            self.logger.error(f"执行爬虫任务失败: {e}")
            raise

    def _job_listener(self, event) -> None:
        """任务事件监听器"""
        if event.exception:
            self.logger.error(f"任务执行失败: {event.job_id} - {event.exception}")
        else:
            self.logger.info(f"任务执行成功: {event.job_id}")


def main() -> None:
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("scheduler.log", encoding="utf-8")],
    )

    logger = logging.getLogger(__name__)

    # 检查是否启用定时任务
    config = load_config()
    scheduler_config = getattr(config, "scheduler", {})
    if not scheduler_config.get("enabled", False):
        logger.info("定时任务未启用，退出")
        return

    # 创建并启动调度器
    scheduler = CrawlerScheduler()

    try:
        if scheduler.start():
            logger.info("定时任务调度器运行中...")

            # 保持程序运行
            import time

            while scheduler.is_running:
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止调度器...")
        scheduler.stop()
    except Exception as e:
        logger.error(f"调度器运行异常: {e}")
        scheduler.stop()


if __name__ == "__main__":
    main()
