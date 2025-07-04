from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from ikuyo.core.models import ScheduledJob


class ScheduledJobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, job: ScheduledJob) -> ScheduledJob:
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_by_id(self, job_id: int) -> Optional[ScheduledJob]:
        return self.session.get(ScheduledJob, job_id)

    def get_by_job_id(self, job_id: str) -> Optional[ScheduledJob]:
        statement = select(ScheduledJob).where(ScheduledJob.job_id == job_id)
        return self.session.exec(statement).first()

    def list(self, limit: int = 0, offset: int = 0) -> List[ScheduledJob]:
        statement = select(ScheduledJob).offset(offset).limit(limit)
        return list(self.session.exec(statement))

    def update(self, job: ScheduledJob) -> ScheduledJob:
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def delete(self, job_id: int) -> None:
        job = self.get_by_id(job_id)
        if job:
            self.session.delete(job)
            self.session.commit()

    def list_enabled(
        self, enabled: bool = True, limit: int = 100, offset: int = 0
    ) -> List[ScheduledJob]:
        statement = (
            select(ScheduledJob)
            .where(ScheduledJob.enabled == enabled)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def list_by_time_range(
        self, start: datetime, end: datetime, limit: int = 100, offset: int = 0
    ) -> List[ScheduledJob]:
        statement = (
            select(ScheduledJob)
            .where(ScheduledJob.created_at is not None)
            .where(ScheduledJob.created_at >= start)  # type: ignore
            .where(ScheduledJob.created_at <= end)  # type: ignore
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement))
