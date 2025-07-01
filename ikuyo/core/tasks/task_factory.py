from ikuyo.core.tasks.crawler_task import CrawlerTask
from ikuyo.core.models.crawler_task import CrawlerTask as CrawlerTaskModel
import json


class TaskFactory:
    """
    任务工厂，根据任务类型和参数动态创建任务对象。
    """

    @staticmethod
    def create_task(
        task_type: str,
        parameters=None,
        repository=None,
        spider_runner=None,
        task_type_db="manual",
        task_record=None,
    ):
        if task_type == "crawler":
            if repository is None:
                raise ValueError("TaskFactory.create_task: repository参数必须传递且非None")
            if task_record is None:
                # 自动创建并持久化数据库记录
                if isinstance(parameters, dict):
                    param_str = json.dumps(parameters)
                else:
                    param_str = parameters or "{}"
                task_record = CrawlerTaskModel(
                    task_type=task_type_db,
                    status="pending",
                    parameters=param_str,
                )
                repository.create(task_record)
            return CrawlerTask(repository, task_record, spider_runner)
        # 未来可扩展其他任务类型
        raise ValueError(f"未知的任务类型: {task_type}")
