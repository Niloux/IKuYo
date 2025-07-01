from typing import Optional, List
from sqlmodel import Session, select
from ikuyo.core.models import CrawlLog


class CrawlLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, log: CrawlLog) -> CrawlLog:
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def get_by_id(self, log_id: int) -> Optional[CrawlLog]:
        return self.session.get(CrawlLog, log_id)

    def list(self, limit: int = 100, offset: int = 0) -> List[CrawlLog]:
        statement = select(CrawlLog).offset(offset).limit(limit)
        return list(self.session.exec(statement))

    def update(self, log: CrawlLog) -> CrawlLog:
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def delete(self, log_id: int) -> None:
        log = self.get_by_id(log_id)
        if log:
            self.session.delete(log)
            self.session.commit()

    def list_by_spider(
        self, spider_name: str, limit: int = 100, offset: int = 0
    ) -> List[CrawlLog]:
        statement = (
            select(CrawlLog).where(CrawlLog.spider_name == spider_name).offset(offset).limit(limit)
        )
        return list(self.session.exec(statement))

    def list_by_mikan_id(self, mikan_id: int, limit: int = 100, offset: int = 0) -> List[CrawlLog]:
        statement = (
            select(CrawlLog).where(CrawlLog.mikan_id == mikan_id).offset(offset).limit(limit)
        )
        return list(self.session.exec(statement))
