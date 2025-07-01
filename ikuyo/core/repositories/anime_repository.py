from typing import Optional, List
from sqlmodel import Session, select
from ikuyo.core.models import Anime
from sqlalchemy import func


class AnimeRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, anime: Anime) -> Anime:
        self.session.add(anime)
        self.session.commit()
        self.session.refresh(anime)
        return anime

    def get_by_id(self, mikan_id: int) -> Optional[Anime]:
        return self.session.get(Anime, mikan_id)

    def list(self, limit: int = 100, offset: int = 0) -> List[Anime]:
        statement = select(Anime).offset(offset).limit(limit)
        return list(self.session.exec(statement))

    def update(self, anime: Anime) -> Anime:
        self.session.add(anime)
        self.session.commit()
        self.session.refresh(anime)
        return anime

    def delete(self, mikan_id: int) -> None:
        anime = self.get_by_id(mikan_id)
        if anime:
            self.session.delete(anime)
            self.session.commit()

    def search_by_title(self, title: str, limit: int = 12, offset: int = 0) -> List[Anime]:
        statement = (
            select(Anime)
            .where(func.lower(Anime.title).like(f"%{title.lower()}%"))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement))
