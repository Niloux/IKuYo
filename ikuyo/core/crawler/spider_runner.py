#!/usr/bin/env python3
"""
爬虫执行器
进程安全的Scrapy爬虫执行模块，支持进度汇报和异常处理
"""

import logging
import traceback
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
            return {
                "task_id": task_id,
                "status": "failed",
                "result": None,
                "error": str(e),
            }

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
            mode=self.config.get("crawler_mode", self.config.get("mode", "homepage")),
            year=self.config.get("year"),
            season=self.config.get("season"),
            start_url=self.config.get("start_url"),
            limit=self.config.get("limit"),
            log_level=self.config.get("log_level", "INFO"),
        )

    def _setup_logging(self, log_level: str):
        """设置日志级别"""
        # 确保 SpiderRunner 自身的日志级别被设置
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    def _run_scrapy(self, config: SpiderConfig) -> str:
        """执行Scrapy爬虫"""
        try:
            import subprocess
            import json
            import sys
            import os

            # Construct the path to the single spider runner script
            script_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "..", "scripts", "run_single_spider.py"
            )
            script_path = os.path.abspath(script_path)

            # Prepare parameters for the subprocess
            # self.config already contains the parameters passed to SpiderRunner
            parameters_json = json.dumps(self.config)

            command = [
                sys.executable,  # Use the current Python interpreter
                script_path,
                str(self.task_id),
                parameters_json,
            ]

            self.logger.info(f"Executing Scrapy spider in new process: {' '.join(command)}")

            # Execute the script in a new subprocess
            # capture_output=True to get stdout/stderr
            # text=True to decode stdout/stderr as text
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False  # Do not raise CalledProcessError for non-zero exit codes
            )

            if result.returncode != 0:
                self.logger.error(f"Subprocess for task {self.task_id} failed with exit code {result.returncode}")
                self.logger.error(f"Subprocess stdout: {result.stdout}")
                self.logger.error(f"Subprocess stderr: {result.stderr}")
                # Attempt to parse error from stdout if available
                try:
                    subprocess_output = json.loads(result.stdout)
                    error_message = subprocess_output.get("error", "Unknown error from subprocess")
                    traceback_info = subprocess_output.get("traceback", "")
                except json.JSONDecodeError:
                    error_message = f"Subprocess failed. Stderr: {result.stderr or 'No stderr'}"
                    traceback_info = ""

                raise Exception(f"Scrapy spider subprocess failed: {error_message}\n{traceback_info}")

            try:
                subprocess_output = json.loads(result.stdout)
                if not subprocess_output.get("success"):
                    error_message = subprocess_output.get("error", "Scrapy spider reported failure")
                    traceback_info = subprocess_output.get("traceback", "")
                    raise Exception(f"Scrapy spider reported failure: {error_message}\n{traceback_info}")
                return subprocess_output.get("message", f"爬虫任务 {self.task_id} 执行成功")
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON output from subprocess: {result.stdout}")
                raise Exception(f"Invalid output from Scrapy spider subprocess. Raw output: {result.stdout}")

        except Exception as e:
            self.logger.error(f"Scrapy执行异常: {e}")
            self.logger.error(traceback.format_exc())  # 记录完整的堆栈跟踪
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
