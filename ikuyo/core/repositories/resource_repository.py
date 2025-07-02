from typing import Optional, List
from sqlmodel import Session, select, col
from ikuyo.core.models import Resource
from sqlalchemy import and_, func


class ResourceRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, resource: Resource) -> Resource:
        self.session.add(resource)
        self.session.commit()
        self.session.refresh(resource)
        return resource

    def get_by_id(self, resource_id: int) -> Optional[Resource]:
        return self.session.get(Resource, resource_id)

    def list(self, limit: int = 100, offset: int = 0) -> List[Resource]:
        statement = (
            select(Resource)
            .order_by(col(Resource.release_date).desc())  # 默认按release_date倒序
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def update(self, resource: Resource) -> Resource:
        self.session.add(resource)
        self.session.commit()
        self.session.refresh(resource)
        return resource

    def delete(self, resource_id: int) -> None:
        resource = self.get_by_id(resource_id)
        if resource:
            self.session.delete(resource)
            self.session.commit()

    def filter(
        self,
        mikan_id: int,
        resolution: Optional[str] = None,
        episode_number: Optional[int] = None,
        subtitle_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Resource]:
        conditions = []
        conditions.append(Resource.mikan_id == mikan_id)
        if resolution is not None:
            conditions.append(Resource.resolution == resolution)
        if episode_number is not None:
            conditions.append(Resource.episode_number == episode_number)
        if subtitle_type is not None:
            conditions.append(Resource.subtitle_type == subtitle_type)
        statement = select(Resource)
        if conditions:
            statement = statement.where(and_(*conditions))
        statement = statement.order_by(col(Resource.release_date).desc())  # 默认按release_date倒序
        if limit:
            statement = statement.limit(limit)
        return list(self.session.exec(statement))

    def count_by_episode(self, mikan_id: int) -> List[dict]:
        """
        按mikan_id分组统计每集资源数，返回[{"episode_number": int, "resource_count": int}, ...]
        """
        statement = (
            select(Resource.episode_number, func.count().label("resource_count"))
            .where(Resource.mikan_id == mikan_id, Resource.episode_number is not None)
            .group_by(Resource.episode_number)  # type: ignore
            .order_by(Resource.episode_number)  # type: ignore
        )
        result = self.session.exec(statement).all()
        return [
            {"episode_number": row[0], "resource_count": row[1]} for row in result
        ]
