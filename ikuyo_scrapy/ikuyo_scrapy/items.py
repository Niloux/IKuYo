# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AnimeItem(scrapy.Item):
    """动画基础信息"""

    mikan_id = scrapy.Field()
    bangumi_id = scrapy.Field()
    title = scrapy.Field()
    original_title = scrapy.Field()
    broadcast_day = scrapy.Field()
    broadcast_start = scrapy.Field()
    official_website = scrapy.Field()
    bangumi_url = scrapy.Field()
    description = scrapy.Field()
    status = scrapy.Field()
    created_at = scrapy.Field()
    updated_at = scrapy.Field()


class SubtitleGroupItem(scrapy.Item):
    """字幕组信息"""

    id = scrapy.Field()
    name = scrapy.Field()
    last_update = scrapy.Field()
    is_subscribed = scrapy.Field()
    created_at = scrapy.Field()


class ResourceItem(scrapy.Item):
    """资源文件信息"""

    mikan_id = scrapy.Field()
    subtitle_group_id = scrapy.Field()
    episode_number = scrapy.Field()
    title = scrapy.Field()
    file_size = scrapy.Field()
    resolution = scrapy.Field()
    subtitle_type = scrapy.Field()
    download_url = scrapy.Field()
    magnet_url = scrapy.Field()
    torrent_url = scrapy.Field()
    play_url = scrapy.Field()
    magnet_hash = scrapy.Field()
    release_date = scrapy.Field()
    created_at = scrapy.Field()


class CrawlLogItem(scrapy.Item):
    """爬取日志"""

    spider_name = scrapy.Field()
    mikan_id = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()
    items_count = scrapy.Field()
    status = scrapy.Field()
    error_message = scrapy.Field()


class AnimeSubtitleGroupItem(scrapy.Item):
    """动画-字幕组关联"""

    mikan_id = scrapy.Field()
    subtitle_group_id = scrapy.Field()
    last_update = scrapy.Field()
