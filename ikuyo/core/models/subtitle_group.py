from typing import Optional
from sqlmodel import SQLModel, Field


class SubtitleGroup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    last_update: Optional[int] = None
    created_at: Optional[int] = None
