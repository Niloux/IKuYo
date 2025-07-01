from typing import Optional, List
from sqlmodel import Session, select
from ikuyo.core.models import Resource
from sqlalchemy import and_, desc


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
        statement = select(Resource).offset(offset).limit(limit)
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
        mikan_id: Optional[int] = None,
        resolution: Optional[str] = None,
        episode_number: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Resource]:
        conditions = []
        if mikan_id is not None:
            conditions.append(Resource.mikan_id == mikan_id)
        if resolution is not None:
            conditions.append(Resource.resolution == resolution)
        if episode_number is not None:
            conditions.append(Resource.episode_number == episode_number)
        statement = select(Resource)
        if conditions:
            statement = statement.where(and_(*conditions))
        statement = statement.order_by(desc(getattr(Resource, 'release_date')))
        if limit:
            statement = statement.limit(limit)
        return list(self.session.exec(statement))
