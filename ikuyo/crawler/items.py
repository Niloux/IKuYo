import scrapy


class AnimeItem(scrapy.Item):
    """动画基础信息"""

    mikan_id = scrapy.Field()
    bangumi_id = scrapy.Field()
    title = scrapy.Field()
    original_title = scrapy.Field()
    broadcast_day = scrapy.Field()
    broadcast_start = scrapy.Field()  # 存储时间戳
    official_website = scrapy.Field()
    bangumi_url = scrapy.Field()
    description = scrapy.Field()
    status = scrapy.Field()
    created_at = scrapy.Field()  # 存储时间戳
    updated_at = scrapy.Field()  # 存储时间戳


class SubtitleGroupItem(scrapy.Item):
    """字幕组信息"""

    id = scrapy.Field()
    name = scrapy.Field()
    last_update = scrapy.Field()  # 存储时间戳
    created_at = scrapy.Field()  # 存储时间戳


class ResourceItem(scrapy.Item):
    """资源文件信息"""

    mikan_id = scrapy.Field()
    subtitle_group_id = scrapy.Field()
    episode_number = scrapy.Field()  # 现在会被填充
    title = scrapy.Field()
    file_size = scrapy.Field()
    resolution = scrapy.Field()  # 新增：从title解析
    subtitle_type = scrapy.Field()  # 新增：从title解析
    # download_url = scrapy.Field()     # 删除：冗余字段
    magnet_url = scrapy.Field()
    torrent_url = scrapy.Field()
    play_url = scrapy.Field()
    magnet_hash = scrapy.Field()
    release_date = scrapy.Field()  # 存储时间戳
    created_at = scrapy.Field()  # 存储时间戳
    updated_at = scrapy.Field()  # 新增：存储时间戳


class CrawlLogItem(scrapy.Item):
    """爬取日志"""

    spider_name = scrapy.Field()
    mikan_id = scrapy.Field()
    start_time = scrapy.Field()  # 存储时间戳
    end_time = scrapy.Field()  # 存储时间戳
    items_count = scrapy.Field()
    status = scrapy.Field()
    error_message = scrapy.Field()
    crawl_mode = scrapy.Field()
    crawl_year = scrapy.Field()
    crawl_season = scrapy.Field()
    reason = scrapy.Field()
    created_at = scrapy.Field()  # 新增：存储时间戳


class AnimeSubtitleGroupItem(scrapy.Item):
    """动画-字幕组关联"""

    mikan_id = scrapy.Field()
    subtitle_group_id = scrapy.Field()
    first_release_date = scrapy.Field()  # 时间戳
    last_update_date = scrapy.Field()  # 时间戳
    resource_count = scrapy.Field()
    is_active = scrapy.Field()
    created_at = scrapy.Field()  # 时间戳
    updated_at = scrapy.Field()  # 时间戳
