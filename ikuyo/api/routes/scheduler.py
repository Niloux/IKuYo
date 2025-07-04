import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ikuyo.api.models.schemas import (
    ScheduledJobCreate,
    ScheduledJobResponse,
    ScheduledJobUpdate,
)
from ikuyo.core.database import get_session
from ikuyo.core.models.scheduled_job import ScheduledJob
from ikuyo.core.repositories.scheduled_job_repository import ScheduledJobRepository
from ikuyo.core.scheduler import unified_scheduler

router = APIRouter(prefix="/scheduler/jobs", tags=["scheduler-jobs"])


def get_repo():
    session = get_session()
    try:
        repo = ScheduledJobRepository(session)
        yield repo
    finally:
        session.close()


@router.get("", response_model=List[ScheduledJobResponse])
def list_jobs(repo: ScheduledJobRepository = Depends(get_repo)):
    jobs = repo.list()
    return [ScheduledJobResponse(**j.model_dump()) for j in jobs]


@router.post("", response_model=ScheduledJobResponse)
def create_job(
    job: ScheduledJobCreate, repo: ScheduledJobRepository = Depends(get_repo)
):
    # 序列化参数为JSON字符串
    job_data = job.model_dump()
    if job_data.get("parameters"):
        # 从参数中提取crawler_mode
        params = job_data["parameters"]
        job_data["crawler_mode"] = params.get("mode", "homepage")
        job_data["parameters"] = json.dumps(params)
    job_obj = ScheduledJob(**job_data)
    created = repo.create(job_obj)
    # 重新加载调度器任务
    if unified_scheduler:
        unified_scheduler.reload_jobs()
    # 反序列化参数用于响应
    created_dict = created.model_dump()
    if created_dict.get("parameters"):
        created_dict["parameters"] = json.loads(created_dict["parameters"])
    return ScheduledJobResponse(**created_dict)


@router.put("/{job_id}", response_model=ScheduledJobResponse)
def update_job(
    job_id: str,
    job: ScheduledJobUpdate,
    repo: ScheduledJobRepository = Depends(get_repo),
):
    db_job = repo.get_by_job_id(job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    # 更新字段
    update_data = job.model_dump(exclude_unset=True)
    if "parameters" in update_data and update_data["parameters"]:
        update_data["parameters"] = json.dumps(update_data["parameters"])
    for field, value in update_data.items():
        setattr(db_job, field, value)
    repo.update(db_job)
    # 重新加载调度器任务
    if unified_scheduler:
        unified_scheduler.reload_jobs()
    # 反序列化参数用于响应
    response_dict = db_job.model_dump()
    if response_dict.get("parameters"):
        response_dict["parameters"] = json.loads(response_dict["parameters"])
    return ScheduledJobResponse(**response_dict)


@router.delete("/{job_id}", response_model=ScheduledJobResponse)
def delete_job(job_id: str, repo: ScheduledJobRepository = Depends(get_repo)):
    db_job = repo.get_by_job_id(job_id)
    if not db_job or db_job.id is None:
        raise HTTPException(status_code=404, detail="Job not found")
    # 反序列化参数用于响应
    response_dict = db_job.model_dump()
    if response_dict.get("parameters"):
        response_dict["parameters"] = json.loads(response_dict["parameters"])
    repo.delete(db_job.id)
    # 重新加载调度器任务
    if unified_scheduler:
        unified_scheduler.reload_jobs()
    return ScheduledJobResponse(**response_dict)


@router.post("/{job_id}/toggle", response_model=ScheduledJobResponse)
def toggle_job(job_id: str, repo: ScheduledJobRepository = Depends(get_repo)):
    db_job = repo.get_by_job_id(job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    db_job.enabled = not db_job.enabled
    repo.update(db_job)
    # 重新加载调度器任务
    if unified_scheduler:
        unified_scheduler.reload_jobs()
    # 反序列化参数用于响应
    response_dict = db_job.model_dump()
    if response_dict.get("parameters"):
        response_dict["parameters"] = json.loads(response_dict["parameters"])
    return ScheduledJobResponse(**response_dict)
