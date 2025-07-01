from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ikuyo.core.database import get_session
from ikuyo.core.repositories.scheduled_job_repository import ScheduledJobRepository
from ikuyo.core.models.scheduled_job import ScheduledJob
from ikuyo.api.models.schemas import ScheduledJobCreate, ScheduledJobUpdate, ScheduledJobResponse

router = APIRouter(prefix="/api/v1/scheduler/jobs", tags=["scheduler-jobs"])


def get_repo():
    session = get_session()
    try:
        repo = ScheduledJobRepository(session)
        yield repo
    finally:
        session.close()


@router.get("", response_model=List[ScheduledJobResponse])
def list_jobs(repo: ScheduledJobRepository = Depends(get_repo)):
    jobs = repo.list(limit=100)
    return [ScheduledJobResponse(**j.model_dump()) for j in jobs]


@router.post("", response_model=ScheduledJobResponse)
def create_job(job: ScheduledJobCreate, repo: ScheduledJobRepository = Depends(get_repo)):
    job_obj = ScheduledJob(**job.model_dump())
    created = repo.create(job_obj)
    return ScheduledJobResponse(**created.model_dump())


@router.put("/{job_id}", response_model=ScheduledJobResponse)
def update_job(
    job_id: str, job: ScheduledJobUpdate, repo: ScheduledJobRepository = Depends(get_repo)
):
    db_job = repo.get_by_job_id(job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    # 更新字段
    for field, value in job.model_dump(exclude_unset=True).items():
        setattr(db_job, field, value)
    repo.update(db_job)
    return ScheduledJobResponse(**db_job.model_dump())


@router.delete("/{job_id}", response_model=ScheduledJobResponse)
def delete_job(job_id: str, repo: ScheduledJobRepository = Depends(get_repo)):
    db_job = repo.get_by_job_id(job_id)
    if not db_job or db_job.id is None:
        raise HTTPException(status_code=404, detail="Job not found")
    repo.delete(db_job.id)
    return ScheduledJobResponse(**db_job.model_dump())


@router.post("/{job_id}/toggle", response_model=ScheduledJobResponse)
def toggle_job(job_id: str, repo: ScheduledJobRepository = Depends(get_repo)):
    db_job = repo.get_by_job_id(job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    db_job.enabled = not db_job.enabled
    repo.update(db_job)
    return ScheduledJobResponse(**db_job.model_dump())
