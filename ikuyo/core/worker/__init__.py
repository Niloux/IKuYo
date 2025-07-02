"""
工作器核心模块
提供多进程并发执行爬虫任务的能力
"""

try:
    from .main import WorkerManager
    from .process_pool import ProcessPool
    from .task_dispatcher import TaskDispatcher

    __all__ = ["WorkerManager", "ProcessPool", "TaskDispatcher"]
except ImportError:
    # 在模块创建阶段可能出现导入错误，忽略
    __all__ = []
