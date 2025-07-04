import time
from typing import Optional

from sqlmodel import Field, SQLModel


class UserSubscription(SQLModel, table=True):
    __tablename__: str = "user_subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, description="用户UUID")
    bangumi_id: int = Field(index=True, description="番剧ID")
    subscribed_at: int = Field(default_factory=lambda: int(time.time()))
    notes: Optional[str] = Field(default=None, description="用户备注")

    # 缓存番剧关键数据用于排序
    anime_name: Optional[str] = Field(default=None, description="番剧原名")
    anime_name_cn: Optional[str] = Field(default=None, description="番剧中文名")
    anime_rating: Optional[float] = Field(default=None, description="番剧评分")
    anime_air_date: Optional[str] = Field(default=None, description="首播日期")
    anime_air_weekday: Optional[int] = Field(default=None, description="播出星期")
