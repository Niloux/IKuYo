from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Index


class Resource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mikan_id: int = Field(foreign_key="anime.mikan_id", index=True)
    subtitle_group_id: int = Field(foreign_key="subtitlegroup.id", index=True)
    episode_number: Optional[int] = Field(index=True)
    title: str = Field(index=True)
    file_size: Optional[str] = None
    resolution: Optional[str] = Field(index=True)
    subtitle_type: Optional[str] = Field(index=True)
    magnet_url: Optional[str] = None
    torrent_url: Optional[str] = None
    play_url: Optional[str] = None
    magnet_hash: Optional[str] = None
    release_date: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    class Config:
        table_args = (
            Index(
                "idx_release_date_desc",
                "release_date",
                postgresql_ops={"release_date": "DESC NULLS LAST"},
            ),
        )
