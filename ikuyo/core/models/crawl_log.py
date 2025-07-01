from typing import Optional
from sqlmodel import SQLModel, Field


class CrawlLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    spider_name: str
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    status: Optional[str] = None
    items_count: Optional[int] = Field(default=0)
    mikan_id: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[int] = None
 