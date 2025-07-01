from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class CrawlerTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_type: str  # 'manual' 或 'scheduled'
    status: str  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    parameters: Optional[str] = Field(default=None)
    result_summary: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    progress: Optional[str] = Field(default=None)
