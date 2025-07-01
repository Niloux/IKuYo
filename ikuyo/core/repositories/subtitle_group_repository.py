from typing import Optional, List
from sqlmodel import Session, select
from ikuyo.core.models import SubtitleGroup


class SubtitleGroupRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, group: SubtitleGroup) -> SubtitleGroup:
        self.session.add(group)
        self.session.commit()
        self.session.refresh(group)
        return group

    def get_by_id(self, group_id: int) -> Optional[SubtitleGroup]:
        return self.session.get(SubtitleGroup, group_id)

    def list(self, limit: int = 100, offset: int = 0) -> List[SubtitleGroup]:
        statement = select(SubtitleGroup).offset(offset).limit(limit)
        return list(self.session.exec(statement))

    def update(self, group: SubtitleGroup) -> SubtitleGroup:
        self.session.add(group)
        self.session.commit()
        self.session.refresh(group)
        return group

    def delete(self, group_id: int) -> None:
        group = self.get_by_id(group_id)
        if group:
            self.session.delete(group)
            self.session.commit()

    def get_by_name(self, name: str) -> Optional[SubtitleGroup]:
        statement = select(SubtitleGroup).where(SubtitleGroup.name == name)
        result = self.session.exec(statement).first()
        return result
