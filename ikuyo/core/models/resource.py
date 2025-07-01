from typing import Optional
from sqlmodel import SQLModel, Field


class Resource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mikan_id: int = Field(foreign_key="anime.mikan_id")
    subtitle_group_id: int = Field(foreign_key="subtitlegroup.id")
    episode_number: Optional[int] = None
    title: str
    file_size: Optional[str] = None
    resolution: Optional[str] = None
    subtitle_type: Optional[str] = None
    magnet_url: Optional[str] = None
    torrent_url: Optional[str] = None
    play_url: Optional[str] = None
    magnet_hash: Optional[str] = None
    release_date: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
 