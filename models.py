import datetime
from typing import Optional


# 动画基础信息表
class Anime:
    def __init__(
        self,
        mikan_id: int,
        bangumi_id: Optional[int],
        title: str,
        original_title: Optional[str] = None,
        broadcast_day: Optional[str] = None,
        broadcast_start: Optional[str] = None,
        official_website: Optional[str] = None,
        bangumi_url: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.mikan_id = mikan_id
        self.bangumi_id = bangumi_id
        self.title = title
        self.original_title = original_title
        self.broadcast_day = broadcast_day
        self.broadcast_start = broadcast_start
        self.official_website = official_website
        self.bangumi_url = bangumi_url
        self.description = description
        self.status = status
        self.created_at = created_at or datetime.datetime.now().isoformat()
        self.updated_at = updated_at or datetime.datetime.now().isoformat()


# 字幕组信息表
class SubtitleGroup:
    def __init__(
        self,
        name: str,
        last_update: Optional[str] = None,
        is_subscribed: bool = False,
        created_at: Optional[str] = None,
    ):
        self.name = name
        self.last_update = last_update
        self.is_subscribed = is_subscribed
        self.created_at = created_at or datetime.datetime.now().isoformat()


# 动画-字幕组关联表
class AnimeSubtitleGroup:
    def __init__(self, anime_id: int, subtitle_group_id: int, last_update: Optional[str] = None):
        self.anime_id = anime_id
        self.subtitle_group_id = subtitle_group_id
        self.last_update = last_update


# 资源文件表
class Resource:
    def __init__(
        self,
        anime_id: int,
        subtitle_group_id: int,
        episode_number: int,
        title: str,
        file_size: Optional[str] = None,
        resolution: Optional[str] = None,
        subtitle_type: Optional[str] = None,
        download_url: Optional[str] = None,
        magnet_hash: Optional[str] = None,
        release_date: Optional[str] = None,
        created_at: Optional[str] = None,
    ):
        self.anime_id = anime_id
        self.subtitle_group_id = subtitle_group_id
        self.episode_number = episode_number
        self.title = title
        self.file_size = file_size
        self.resolution = resolution
        self.subtitle_type = subtitle_type
        self.download_url = download_url
        self.magnet_hash = magnet_hash
        self.release_date = release_date
        self.created_at = created_at or datetime.datetime.now().isoformat()


# 爬取日志表
class CrawlLog:
    def __init__(
        self,
        spider_name: str,
        anime_id: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        items_count: int = 0,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        self.spider_name = spider_name
        self.anime_id = anime_id
        self.start_time = start_time or datetime.datetime.now().isoformat()
        self.end_time = end_time
        self.items_count = items_count
        self.status = status
        self.error_message = error_message
