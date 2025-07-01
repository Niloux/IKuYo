from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List
from ikuyo.core.database import get_session
from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.tasks.task_factory import TaskFactory
from ikuyo.api.models.schemas import CrawlerTaskCreate, CrawlerTaskResponse
import asyncio
import json
from ikuyo.core.models.crawler_task import CrawlerTask

router = APIRouter(prefix="/api/v1/crawler/tasks", tags=["crawler-tasks"])

# 依赖注入：获取数据库Session


def get_repo():
    session = get_session()
    try:
        repo = CrawlerTaskRepository(session)
        yield repo
    finally:
        session.close()


def _to_response(t: CrawlerTask) -> CrawlerTaskResponse:
    try:
        progress = json.loads(t.progress) if t.progress else None
    except Exception:
        progress = t.progress
    return CrawlerTaskResponse(
        id=t.id,
        status=t.status,
        created_at=t.created_at,
        started_at=t.started_at,
        completed_at=t.completed_at,
        parameters=t.parameters,
        result_summary=t.result_summary,
        error_message=t.error_message,
        progress=progress,
    )


@router.post("", response_model=CrawlerTaskResponse)
async def create_task(
    params: CrawlerTaskCreate,
    repo: CrawlerTaskRepository = Depends(get_repo),
):
    task = TaskFactory.create_task(
        task_type="crawler",
        parameters=params.model_dump(),
        repository=repo,
        spider_runner=None,
        task_type_db="manual",
    )
    await task.execute()
    t = task.task_record
    return _to_response(t)


@router.get("", response_model=List[CrawlerTaskResponse])
def list_tasks(repo: CrawlerTaskRepository = Depends(get_repo)):
    tasks = repo.list(limit=100)
    return [_to_response(t) for t in tasks]


@router.get("/{task_id}", response_model=CrawlerTaskResponse)
def get_task(task_id: int, repo: CrawlerTaskRepository = Depends(get_repo)):
    t = repo.get_by_id(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_response(t)


@router.delete("/{task_id}", response_model=CrawlerTaskResponse)
async def cancel_task(task_id: int, repo: CrawlerTaskRepository = Depends(get_repo)):
    t = repo.get_by_id(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    # 调用任务对象的cancel方法，确保进程池强制kill
    task = TaskFactory.create_task(
        task_type="crawler",
        parameters=t.parameters,
        repository=repo,
        spider_runner=None,
        task_type_db=t.task_type,
        task_record=t,
    )
    await task.cancel()
    repo.update(t)
    return _to_response(t)


@router.get("/{task_id}/progress")
def get_task_progress(task_id: int, repo: CrawlerTaskRepository = Depends(get_repo)):
    t = repo.get_by_id(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    # 返回progress字段内容
    progress = t.progress
    return {"task_id": t.id, "progress": progress}


# WebSocket接口：实时推送任务进度
@router.websocket("/ws/crawler/tasks/{task_id}")
async def websocket_task_progress(websocket: WebSocket, task_id: int):
    await websocket.accept()
    try:
        last_progress = None
        while True:
            # 轮询数据库进度字段
            await asyncio.sleep(1)
            with get_session() as session:
                repo = CrawlerTaskRepository(session)
                t = repo.get_by_id(task_id)
                if not t:
                    await websocket.send_json({"error": "Task not found"})
                    break
                progress = t.progress
                if progress != last_progress:
                    try:
                        msg = json.loads(progress) if progress else {}
                    except Exception:
                        msg = {"progress": progress}
                    await websocket.send_json(msg)
                    last_progress = progress
                if t.status in ("completed", "failed", "cancelled"):
                    break
    except WebSocketDisconnect:
        pass
