from typing import Optional, Tuple

from sqlmodel import Session, asc, desc, or_, select

from ikuyo.core.models.user_subscription import UserSubscription


class SubscriptionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, subscription: UserSubscription) -> UserSubscription:
        """创建新的订阅记录"""
        self.session.add(subscription)
        self.session.commit()
        self.session.refresh(subscription)
        return subscription

    def get_by_user_and_bangumi(self, user_id: str, bangumi_id: int) -> Optional[UserSubscription]:
        """根据用户ID和番剧ID获取订阅记录"""
        return self.session.exec(
            select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.bangumi_id == bangumi_id
            )
        ).first()

    def get_subscriptions_with_sort_and_search(
        self,
        user_id: str,
        sort: str = "subscribed_at",
        order: str = "desc",
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[list[UserSubscription], int]:
        """获取用户订阅列表，支持排序、搜索、分页"""

        # 构建查询
        query = select(UserSubscription).where(UserSubscription.user_id == user_id)

        # 搜索条件
        if search:
            query = query.where(
                or_(
                    UserSubscription.anime_name.like(f"%{search}%"),  # type: ignore
                    UserSubscription.anime_name_cn.like(f"%{search}%")  # type: ignore
                )
            )

        # 排序条件映射
        sort_mapping = {
            "subscribed_at": UserSubscription.subscribed_at,
            "rating": UserSubscription.anime_rating,
            "air_date": UserSubscription.anime_air_date,
            "name": UserSubscription.anime_name_cn
        }

        sort_field = sort_mapping.get(sort, UserSubscription.subscribed_at)
        if order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))

        # 获取总数
        total = len(self.session.exec(query).all())

        # 分页
        subscriptions = list(self.session.exec(
            query.offset((page - 1) * limit).limit(limit)
        ).all())

        return subscriptions, total

    def delete_by_user_and_bangumi(self, user_id: str, bangumi_id: int) -> bool:
        """删除指定用户的指定番剧订阅"""
        subscription = self.get_by_user_and_bangumi(user_id, bangumi_id)
        if subscription:
            self.session.delete(subscription)
            self.session.commit()
            return True
        return False
