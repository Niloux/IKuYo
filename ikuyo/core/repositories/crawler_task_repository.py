from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, desc, select

from ikuyo.core.models import CrawlerTask


class CrawlerTaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, task: CrawlerTask) -> CrawlerTask:
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_by_id(self, task_id: int) -> Optional[CrawlerTask]:
        return self.session.get(CrawlerTask, task_id)

    def list(self, limit: int = 10, offset: int = 0) -> List[CrawlerTask]:
        statement = (
            select(CrawlerTask)
            .order_by(desc(CrawlerTask.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def update(self, task: CrawlerTask) -> CrawlerTask:
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def delete(self, task_id: int) -> None:
        task = self.get_by_id(task_id)
        if task:
            self.session.delete(task)
            self.session.commit()

    def list_by_status(
        self, status: str, limit: int = 100, offset: int = 0
    ) -> List[CrawlerTask]:
        statement = (
            select(CrawlerTask)
            .where(CrawlerTask.status == status)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def list_by_type(
        self, task_type: str, limit: int = 100, offset: int = 0
    ) -> List[CrawlerTask]:
        statement = (
            select(CrawlerTask)
            .where(CrawlerTask.task_type == task_type)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def list_by_time_range(
        self, start: datetime, end: datetime, limit: int = 100, offset: int = 0
    ) -> List[CrawlerTask]:
        statement = (
            select(CrawlerTask)
            .where(CrawlerTask.created_at is not None)
            .where(CrawlerTask.created_at >= start)  # type: ignore
            .where(CrawlerTask.created_at <= end)  # type: ignore
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement))
