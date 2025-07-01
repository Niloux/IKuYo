from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
from ikuyo.core.database import get_session
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.tasks.task_factory import TaskFactory
from ikuyo.api.models.schemas import CrawlerTaskCreate, CrawlerTaskResponse
import asyncio
from ikuyo.core.crawler_runner import AsyncSpiderRunner

router = APIRouter(prefix="/api/v1/crawler/tasks", tags=["crawler-tasks"])

# 依赖注入：获取数据库Session


def get_repo():
    session = get_session()
    try:
        repo = CrawlerTaskRepository(session)
        yield repo
    finally:
        session.close()


# 依赖注入：获取全局 spider_runner

def get_spider_runner() -> AsyncSpiderRunner:
    from ikuyo.api.app import spider_runner
    return spider_runner


@router.post("", response_model=CrawlerTaskResponse)
async def create_task(
    params: CrawlerTaskCreate,
    repo: CrawlerTaskRepository = Depends(get_repo),
    spider_runner: AsyncSpiderRunner = Depends(get_spider_runner)
):
    task = TaskFactory.create_task(
        task_type="crawler",
        parameters=params.model_dump(),
        repository=repo,
        spider_runner=spider_runner,  # 注入实际spider_runner实例
        task_type_db="manual",
    )
    # 直接 await 执行异步任务
    await task.execute()
    t = task.task_record
    return CrawlerTaskResponse(
        id=t.id,
        status=t.status,
        created_at=t.created_at,
        started_at=t.started_at,
        completed_at=t.completed_at,
        parameters=t.parameters,
        result_summary=t.result_summary,
        error_message=t.error_message,
    )


@router.get("", response_model=List[CrawlerTaskResponse])
def list_tasks(repo: CrawlerTaskRepository = Depends(get_repo)):
    tasks = repo.list(limit=100)
    return [
        CrawlerTaskResponse(
            id=t.id,
            status=t.status,
            created_at=t.created_at,
            started_at=t.started_at,
            completed_at=t.completed_at,
            parameters=t.parameters,
            result_summary=t.result_summary,
            error_message=t.error_message,
        ) for t in tasks
    ]


@router.get("/{task_id}", response_model=CrawlerTaskResponse)
def get_task(task_id: int, repo: CrawlerTaskRepository = Depends(get_repo)):
    t = repo.get_by_id(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return CrawlerTaskResponse(
        id=t.id,
        status=t.status,
        created_at=t.created_at,
        started_at=t.started_at,
        completed_at=t.completed_at,
        parameters=t.parameters,
        result_summary=t.result_summary,
        error_message=t.error_message,
    )


@router.delete("/{task_id}", response_model=CrawlerTaskResponse)
def cancel_task(task_id: int, repo: CrawlerTaskRepository = Depends(get_repo)):
    t = repo.get_by_id(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    # 这里只做状态流转，实际应调度cancel逻辑
    t.status = "cancelled"
    repo.update(t)
    return CrawlerTaskResponse(
        id=t.id,
        status=t.status,
        created_at=t.created_at,
        started_at=t.started_at,
        completed_at=t.completed_at,
        parameters=t.parameters,
        result_summary=t.result_summary,
        error_message=t.error_message,
    )


@router.get("/{task_id}/progress", response_model=CrawlerTaskResponse)
def get_task_progress(task_id: int, repo: CrawlerTaskRepository = Depends(get_repo)):
    t = repo.get_by_id(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    # 进度信息可扩展为更细粒度
    return CrawlerTaskResponse(
        id=t.id,
        status=t.status,
        created_at=t.created_at,
        started_at=t.started_at,
        completed_at=t.completed_at,
        parameters=t.parameters,
        result_summary=t.result_summary,
        error_message=t.error_message,
    )
