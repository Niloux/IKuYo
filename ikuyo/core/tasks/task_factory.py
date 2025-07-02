from ikuyo.core.tasks.crawler_task import CrawlerTask


class TaskFactory:
    """
    任务工厂，根据任务类型和参数动态创建任务对象。
    """

    @staticmethod
    def create_task(
        task_type: str,
        parameters=None,
        repository=None,
        task_type_db="manual",
        task_record=None,
    ):
        if task_type == "crawler":
            if repository is None:
                raise ValueError("TaskFactory.create_task: repository参数必须传递且非None")
            return CrawlerTask(repository, task_record, parameters, task_type_db)
        # 未来可扩展其他任务类型
        raise ValueError(f"未知的任务类型: {task_type}")
