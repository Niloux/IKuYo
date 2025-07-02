from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from typing import List, Union
import asyncio

from ikuyo.core.repositories.crawler_task_repository import CrawlerTaskRepository
from ikuyo.core.models.crawler_task import CrawlerTask as CrawlerTaskModel
from ikuyo.core.tasks.task_factory import TaskFactory
from ikuyo.core.tasks.crawler_task import CrawlerTask
from ikuyo.api.models.schemas import TaskResponse, CrawlerTaskCreate
from ikuyo.core.database import get_session

import json
from ikuyo.core.redis_client import get_redis_connection

router = APIRouter(prefix="/crawler/tasks", tags=["crawler-tasks"])


def get_repo():
    """依赖注入：获取数据库Session和Repository"""
    with get_session() as session:
        repo = CrawlerTaskRepository(session)
        yield repo


def _to_response(t: Union[CrawlerTask, CrawlerTaskModel]) -> TaskResponse:
    """将任务对象转换为响应对象"""
    if isinstance(t, CrawlerTask):
        t = t.task_record
    if t is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="任务创建失败"
        )

    return TaskResponse(
        id=t.id or 0,
        task_type=t.task_type,
        status=t.status,
        parameters=t.parameters,
        result_summary=t.result_summary,
        created_at=t.created_at,
        started_at=t.started_at,
        completed_at=t.completed_at,
        error_message=t.error_message,
        percentage=t.percentage,
        processed_items=t.processed_items,
        total_items=t.total_items,
        processing_speed=t.processing_speed,
        estimated_remaining=t.estimated_remaining,
    )


def _get_task_or_404(task_id: int, repo: CrawlerTaskRepository) -> CrawlerTaskModel:
    """获取任务或返回404错误"""
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"任务 {task_id} 不存在"
        )
    return task


def _get_progress_data(task: CrawlerTaskModel) -> dict:
    """获取任务进度数据"""
    return {
        "task_id": task.id or 0,
        "percentage": task.percentage,
        "processed_items": task.processed_items,
        "total_items": task.total_items,
        "processing_speed": task.processing_speed,
        "estimated_remaining": task.estimated_remaining,
    }


@router.post("", response_model=TaskResponse)
def create_task(
    task_create: CrawlerTaskCreate, repo: CrawlerTaskRepository = Depends(get_repo)
):
    """创建新任务并推送到Redis队列"""
    try:
        # 1. 使用TaskFactory创建任务对象
        task = TaskFactory.create_task(
            task_type="crawler",
            parameters=task_create.model_dump(),
            repository=repo,
            task_type_db="manual",
        )

        # 2. 写入数据库以获取 task_id
        task.write_to_db()
        if not task.task_record or not task.task_record.id:
            raise ValueError("任务记录或任务ID在写入数据库后未能生成")

        task_id = task.task_record.id

        # 3. 将任务ID推送到Redis队列
        try:
            redis_client = get_redis_connection()
            queue_name = "ikuyo:crawl_tasks"
            message = json.dumps({"task_id": task_id})
            redis_client.lpush(queue_name, message)
        except Exception as redis_error:
            # 如果Redis推送失败，这是一个严重问题
            # 将任务标记为失败，因为worker无法接收到它
            task.task_record.status = "failed"
            task.task_record.error_message = (
                f"Failed to publish task to Redis: {redis_error}"
            )
            repo.update(task.task_record)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"任务已创建但无法推送到处理队列: {redis_error}",
            )

        return _to_response(task)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}",
        )


@router.get("", response_model=List[TaskResponse])
def list_tasks(repo: CrawlerTaskRepository = Depends(get_repo)):
    """获取任务列表"""
    try:
        tasks = repo.list(limit=100)
        return [_to_response(t) for t in tasks]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}",
        )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, repo: CrawlerTaskRepository = Depends(get_repo)):
    """获取任务详情"""
    task = _get_task_or_404(task_id, repo)
    return _to_response(task)


@router.delete("/{task_id}", response_model=TaskResponse)
def cancel_task(task_id: int, repo: CrawlerTaskRepository = Depends(get_repo)):
    """取消任务"""
    task = _get_task_or_404(task_id, repo)

    try:
        # 使用TaskFactory创建任务对象
        task_obj = TaskFactory.create_task(
            task_type="crawler",
            parameters=task.parameters,
            repository=repo,
            task_type_db=task.task_type,
            task_record=task,
        )
        # 调用任务对象的取消方法
        task_obj.cancel()
        return _to_response(task)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消任务失败: {str(e)}",
        )


@router.get("/{task_id}/progress")
def get_task_progress(task_id: int, repo: CrawlerTaskRepository = Depends(get_repo)):
    """获取任务进度"""
    task = _get_task_or_404(task_id, repo)
    return _get_progress_data(task)


@router.websocket("/{task_id}/ws")
async def websocket_task_progress(websocket: WebSocket, task_id: int):
    """WebSocket接口获取任务进度"""
    await websocket.accept()
    last_progress = None

    try:
        while True:
            await asyncio.sleep(1)  # 每秒检查一次进度

            try:
                with get_session() as session:
                    repo = CrawlerTaskRepository(session)
                    task = repo.get_by_id(task_id)

                    if not task:
                        await websocket.send_json(
                            {
                                "error": f"任务 {task_id} 不存在",
                                "code": "task_not_found",
                            }
                        )
                        break

                    # 检查进度是否有更新
                    current_progress = _get_progress_data(task)

                    if current_progress != last_progress:
                        await websocket.send_json(current_progress)
                        last_progress = current_progress

                    # 如果任务已完成或失败，发送最终状态并关闭连接
                    if task.status in ["completed", "failed", "cancelled"]:
                        await websocket.send_json(
                            {
                                **current_progress,
                                "final_status": task.status,
                                "result_summary": task.result_summary,
                                "error_message": task.error_message,
                            }
                        )
                        break

            except Exception as e:
                await websocket.send_json(
                    {
                        "error": f"获取任务进度失败: {str(e)}",
                        "code": "internal_error",
                    }
                )
                break

    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
