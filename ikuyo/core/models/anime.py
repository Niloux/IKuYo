from typing import Optional
from sqlmodel import SQLModel, Field


class Anime(SQLModel, table=True):
    mikan_id: Optional[int] = Field(default=None, primary_key=True)
    bangumi_id: Optional[int] = Field(default=None, index=True)
    title: str = Field(index=True)
    original_title: Optional[str] = None
    broadcast_day: Optional[str] = None
    broadcast_start: Optional[int] = None
    official_website: Optional[str] = None
    bangumi_url: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(default="unknown")
    created_at: Optional[int] = None  # Unix时间戳
    updated_at: Optional[int] = None  # Unix时间戳
