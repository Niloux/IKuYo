from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ScheduledJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str
    name: str
    description: Optional[str] = Field(default=None)
    cron_expression: str
    crawler_mode: str
    parameters: Optional[str] = Field(default=None)
    enabled: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
