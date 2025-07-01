from typing import Optional
from sqlmodel import SQLModel, Field


class AnimeSubtitleGroup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mikan_id: int = Field(foreign_key="anime.mikan_id")
    subtitle_group_id: int = Field(foreign_key="subtitlegroup.id")
    first_release_date: Optional[int] = None
    last_update_date: Optional[int] = None
    resource_count: Optional[int] = Field(default=0)
    is_active: Optional[int] = Field(default=1)
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
 