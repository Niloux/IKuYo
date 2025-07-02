#!/usr/bin/env python3
"""
爬虫执行器
进程安全的Scrapy爬虫执行模块，支持进度汇报和异常处理
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SpiderConfig:
    """爬虫配置"""

    mode: str
    year: Optional[int] = None
    season: Optional[str] = None
    start_url: Optional[str] = None
    limit: Optional[int] = None
    log_level: str = "INFO"
    output: Optional[str] = None


class SpiderRunner:
    """
    爬虫执行器
    在独立进程中安全执行Scrapy爬虫
    """

    def __init__(self, task_id: int, config: Dict[str, Any]):
        self.task_id = task_id
        self.config = config
        self.logger = logging.getLogger(f"spider-runner-{task_id}")

    @classmethod
    def execute_in_process(cls, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在独立进程中执行爬虫任务
        这是进程池调用的主要入口点
        """
        task_id = task_data.get("task_id")
        if task_id is None:
            return {
                "task_id": None,
                "status": "failed",
                "result": None,
                "error": "Missing task_id in task_data",
            }

        parameters = task_data.get("parameters", {})

        try:
            # 创建执行器实例
            runner = cls(task_id, parameters)

            # 执行爬虫
            result = runner.run()

            return {
                "task_id": task_id,
                "status": "completed" if result["success"] else "failed",
                "result": result,
                "error": result.get("error") if not result["success"] else None,
            }

        except Exception as e:
            return {"task_id": task_id, "status": "failed", "result": None, "error": str(e)}

    def run(self) -> Dict[str, Any]:
        """执行爬虫任务"""
        try:
            self.logger.info(f"开始执行爬虫任务 {self.task_id}")

            # 解析配置
            spider_config = self._parse_config()

            # 设置日志
            self._setup_logging(spider_config.log_level)

            # 执行爬虫
            result = self._run_scrapy(spider_config)

            self.logger.info(f"爬虫任务 {self.task_id} 执行完成")
            return {"success": True, "result": result}

        except Exception as e:
            self.logger.error(f"爬虫任务 {self.task_id} 执行失败: {e}")
            return {"success": False, "error": str(e)}

    def _parse_config(self) -> SpiderConfig:
        """解析爬虫配置"""
        return SpiderConfig(
            mode=self.config.get("mode", "homepage"),
            year=self.config.get("year"),
            season=self.config.get("season"),
            start_url=self.config.get("start_url"),
            limit=self.config.get("limit"),
            log_level=self.config.get("log_level", "INFO"),
        )

    def _setup_logging(self, log_level: str):
        """设置日志级别"""
        # 为当前进程设置日志级别
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

    def _run_scrapy(self, config: SpiderConfig) -> str:
        """执行Scrapy爬虫"""
        try:
            # 导入Scrapy相关模块
            from scrapy.crawler import CrawlerProcess
            from scrapy.utils.project import get_project_settings
            from ikuyo.crawler.spiders.mikan import MikanSpider
            from ikuyo.core.config import load_config

            # 获取项目配置
            project_config = load_config()

            # 设置Scrapy配置
            settings = get_project_settings()
            settings.set("LOG_LEVEL", config.log_level)

            if config.output:
                settings.set("FEED_FORMAT", "json")
                settings.set("FEED_URI", config.output)

            # 创建爬虫进程
            process = CrawlerProcess(settings)

            # 准备爬虫参数
            spider_kwargs = {"config": project_config, "mode": config.mode}

            if config.year:
                spider_kwargs["year"] = config.year
            if config.season:
                spider_kwargs["season"] = config.season
            if config.start_url:
                spider_kwargs["start_url"] = config.start_url
            if config.limit is not None:
                spider_kwargs["limit"] = config.limit

            self.logger.info(f"启动Scrapy爬虫，参数: {spider_kwargs}")

            # 启动爬虫
            process.crawl(MikanSpider, **spider_kwargs)
            process.start()  # 这会阻塞直到爬虫完成

            return f"爬虫任务 {self.task_id} 执行成功"

        except Exception as e:
            self.logger.error(f"Scrapy执行异常: {e}")
            raise

    def _log_to_file(self, message: str):
        """记录日志到文件"""
        try:
            with open("./worker_debug.log", "a") as f:
                f.write(f"[SPIDER-{self.task_id}] {message}\n")
        except Exception:
            pass  # 忽略日志写入错误


def run_crawler_in_subprocess(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    子进程入口函数
    兼容原有的worker.py调用方式
    """
    return SpiderRunner.execute_in_process(task_data)
