import json
import logging
import threading
import datetime
from typing import Optional
from ikuyo.core.redis_client import get_redis_connection
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.database import get_session

logger = logging.getLogger(__name__)


def start_progress_consumer():
    """
    启动一个线程来消费 Redis 中的爬虫进度更新。
    """
    thread = threading.Thread(target=_consume_progress_updates, daemon=True)
    thread.start()
    logger.info("爬虫进度消费者已启动。")
    return thread


def _consume_progress_updates():
    """
    实际消费 Redis 进度更新的逻辑。
    """
    redis_client = get_redis_connection()
    pubsub = redis_client.pubsub()
    pubsub.psubscribe("crawler_progress:*", "crawler_status:*", "crawler_result:*")
    logger.info("已订阅 Redis 进度、状态和结果频道。")

    for message in pubsub.listen():
        if message["type"] == "pmessage":
            channel = message["channel"]
            data = json.loads(message["data"])
            logger.info(f"Received Redis message on channel {channel}: {data}")  # 新增日志

            try:
                if channel.startswith("crawler_progress:"):
                    task_id = int(channel.split(":")[1])
                    _update_progress_in_db(task_id, data)
                elif channel.startswith("crawler_status:"):
                    task_id = int(channel.split(":")[1])
                    _update_status_in_db(task_id, data["status"], data.get("error_message"))
                elif channel.startswith("crawler_result:"):
                    task_id = int(channel.split(":")[1])
                    _update_result_in_db(task_id, data["result_summary"])
            except Exception as e:
                logger.error(f"处理 Redis 消息时出错: {e}, 消息: {message}")


def _update_progress_in_db(task_id: int, progress_data: dict):
    """
    将进度数据更新到数据库。
    """
    try:
        with get_session() as session:
            repo = CrawlerTaskRepository(session)
            task = repo.get_by_id(task_id)
            if task:
                task.update_progress(
                    percentage=progress_data.get("percentage"),
                    processed_items=progress_data.get("processed_items"),
                    total_items=progress_data.get("total_items"),
                    processing_speed=progress_data.get("processing_speed"),
                    estimated_remaining=progress_data.get("estimated_remaining"),
                )
                repo.update(task)
                logger.debug(f"任务 {task_id} 进度已更新到数据库: {progress_data}")
            else:
                logger.warning(f"任务 {task_id} 不存在，无法更新进度。")
    except Exception as e:
        logger.error(f"更新任务 {task_id} 进度到数据库时出错: {e}")


def _update_status_in_db(task_id: int, status: str, error_message: Optional[str] = None):
    """
    将状态更新到数据库。
    """
    try:
        with get_session() as session:
            repo = CrawlerTaskRepository(session)
            task = repo.get_by_id(task_id)
            if task:
                task.status = status
                if error_message:
                    task.error_message = error_message
                if status in ["completed", "failed", "cancelled"]:
                    task.completed_at = datetime.datetime.now(datetime.timezone.utc)
                repo.update(task)
                logger.info(f"任务 {task_id} 状态已更新到数据库: {status}")
            else:
                logger.warning(f"任务 {task_id} 不存在，无法更新状态。")
    except Exception as e:
        logger.error(f"更新任务 {task_id} 状态到数据库时出错: {e}")


def _update_result_in_db(task_id: int, result_summary: str):
    """
    将结果更新到数据库。
    """
    try:
        with get_session() as session:
            repo = CrawlerTaskRepository(session)
            task = repo.get_by_id(task_id)
            if task:
                task.result_summary = result_summary
                repo.update(task)
                logger.info(f"任务 {task_id} 结果已更新到数据库。")
            else:
                logger.warning(f"任务 {task_id} 不存在，无法更新结果。")
    except Exception as e:
        logger.error(f"更新任务 {task_id} 结果到数据库时出错: {e}")
