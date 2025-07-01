from typing import Optional, List
from sqlmodel import Session, select
from ikuyo.core.models import AnimeSubtitleGroup


class AnimeSubtitleGroupRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, asg: AnimeSubtitleGroup) -> AnimeSubtitleGroup:
        self.session.add(asg)
        self.session.commit()
        self.session.refresh(asg)
        return asg

    def get_by_id(self, asg_id: int) -> Optional[AnimeSubtitleGroup]:
        return self.session.get(AnimeSubtitleGroup, asg_id)

    def list(self, limit: int = 100, offset: int = 0) -> List[AnimeSubtitleGroup]:
        statement = select(AnimeSubtitleGroup).offset(offset).limit(limit)
        return list(self.session.exec(statement))

    def update(self, asg: AnimeSubtitleGroup) -> AnimeSubtitleGroup:
        self.session.add(asg)
        self.session.commit()
        self.session.refresh(asg)
        return asg

    def delete(self, asg_id: int) -> None:
        asg = self.get_by_id(asg_id)
        if asg:
            self.session.delete(asg)
            self.session.commit()

    def get_by_mikan_and_group(
        self, mikan_id: int, subtitle_group_id: int
    ) -> Optional[AnimeSubtitleGroup]:
        statement = select(AnimeSubtitleGroup).where(
            AnimeSubtitleGroup.mikan_id == mikan_id,
            AnimeSubtitleGroup.subtitle_group_id == subtitle_group_id,
        )
        return self.session.exec(statement).first()
