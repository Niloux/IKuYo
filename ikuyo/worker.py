import time
import json
import traceback
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.crawler_runner import run_crawler
from ikuyo.core.database import get_session
from ikuyo.core.config import load_config
import datetime
from datetime import timezone

POLL_INTERVAL = 2  # 轮询间隔（秒）


def log(msg):
    with open("./worker_debug.log", "a") as f:
        f.write(f"[WORKER] {msg}\n")


def main():
    log("Worker started")
    while True:
        with get_session() as session:
            repo = CrawlerTaskRepository(session)
            tasks = repo.list_by_status("pending")
            for task in tasks:
                try:
                    log(f"Found pending task: id={task.id}")
                    # 标记为running
                    task.status = "running"
                    repo.update(task)
                    # 组装args，调用run_crawler
                    params = (
                        json.loads(task.parameters)
                        if isinstance(task.parameters, str)
                        else task.parameters
                    )
                    if not params:
                        log(f"Task id={task.id} has no parameters, skipping")
                        continue

                    class Args:
                        def __init__(
                            self, mode, year, season, start_url, limit, log_level, output
                        ):
                            self.mode = mode
                            self.year = year
                            self.season = season
                            self.start_url = start_url
                            self.limit = limit
                            self.log_level = log_level
                            self.output = output

                    args = Args(
                        params.get("mode"),
                        params.get("year"),
                        params.get("season"),
                        params.get("start_url"),
                        params.get("limit"),
                        "INFO",
                        None,
                    )
                    config = load_config()
                    # 执行爬虫
                    log(f"Starting run_crawler for task id={task.id}")
                    run_crawler(args, config)
                    # 检查任务状态（支持取消）
                    t = repo.get_by_id(int(task.id)) if task.id is not None else None
                    if t and t.status == "cancelled":
                        log(f"Task id={task.id} was cancelled during execution")
                        continue
                    # 标记为completed
                    task.status = "completed"
                    task.completed_at = datetime.datetime.now(timezone.utc)
                    repo.update(task)
                    log(f"Task id={task.id} completed")
                except Exception as e:
                    task.status = "failed"
                    task.error_message = f"{e}\n{traceback.format_exc()}"
                    repo.update(task)
                    log(f"Task id={task.id} failed: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
