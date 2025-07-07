from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlmodel import Session

from ikuyo.core.bangumi_service import BangumiService
from ikuyo.core.database import get_session
from ikuyo.core.models.user_subscription import UserSubscription
from ikuyo.core.repositories.subscription_repository import SubscriptionRepository

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# 创建BangumiService实例
bangumi_service = BangumiService()


def get_user_id(x_user_id: str = Header(..., description="用户UUID")) -> str:
    """从HTTP Header中获取用户ID"""
    return x_user_id


@router.post("/{bangumi_id}")
async def subscribe(
    bangumi_id: int,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session)
):
    """添加订阅"""
    repo = SubscriptionRepository(session)

    # 检查是否已订阅
    if repo.get_by_user_and_bangumi(user_id, bangumi_id):
        raise HTTPException(status_code=400, detail="Already subscribed")

    # 获取番剧信息
    try:
        anime_info = await bangumi_service.get_subject(bangumi_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Anime not found")

    # 创建订阅记录
    subscription = UserSubscription(
        user_id=user_id,
        bangumi_id=bangumi_id,
        anime_name=anime_info.get("name"),  # type: ignore
        anime_name_cn=anime_info.get("name_cn"),  # type: ignore
        anime_rating=anime_info.get("rating", {}).get("score"),  # type: ignore
        anime_air_date=anime_info.get("air_date"),  # type: ignore
        anime_air_weekday=anime_info.get("air_weekday")  # type: ignore
    )

    return repo.create(subscription)


@router.get("")
async def get_subscriptions(
    user_id: str = Depends(get_user_id),
    sort: str = Query("subscribed_at", description="排序字段：subscribed_at|rating|air_date|name"),
    order: str = Query("desc", description="排序方向：asc|desc"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    session: Session = Depends(get_session)
):
    """获取订阅列表"""
    repo = SubscriptionRepository(session)

    subscriptions, total = repo.get_subscriptions_with_sort_and_search(
        user_id=user_id,
        sort=sort,
        order=order,
        search=search,
        page=page,
        limit=limit
    )

    return {
        "subscriptions": subscriptions,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }


@router.delete("/{bangumi_id}")
async def unsubscribe(
    bangumi_id: int,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session)
):
    """取消订阅"""
    repo = SubscriptionRepository(session)
    if not repo.delete_by_user_and_bangumi(user_id, bangumi_id):
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"message": "Unsubscribed successfully"}


@router.get("/ids")
async def get_subscription_ids(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session)
):
    """
    获取当前用户所有已订阅番剧的bangumi_id列表（轻量接口）
    """
    repo = SubscriptionRepository(session)
    ids = repo.get_all_bangumi_ids_by_user(user_id)
    return {"ids": ids}


@router.get("/{bangumi_id}")
async def check_subscription(
    bangumi_id: int,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session)
):
    """检查订阅状态"""
    repo = SubscriptionRepository(session)
    subscription = repo.get_by_user_and_bangumi(user_id, bangumi_id)
    if subscription:
        return {
            "subscribed": True,
            "subscribed_at": subscription.subscribed_at,
            "notes": subscription.notes
        }
    return {"subscribed": False}
