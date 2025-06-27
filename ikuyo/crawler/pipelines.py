#!/usr/bin/env python3
"""
数据处理管道
负责将爬取的数据保存到数据库
更新以支持读写分离架构
"""


from scrapy.exceptions import DropItem

from ..core.database import DatabaseManager
from .items import AnimeItem, AnimeSubtitleGroupItem, CrawlLogItem, ResourceItem, SubtitleGroupItem


class ValidationPipeline:
    """数据验证Pipeline"""

    def process_item(self, item, spider):
        if isinstance(item, AnimeItem):
            if not item.get("mikan_id") or not item.get("title"):
                raise DropItem(f"Missing required fields in AnimeItem: {item}")
        elif isinstance(item, ResourceItem):
            if not item.get("mikan_id") or not item.get("subtitle_group_id"):
                raise DropItem(f"Missing required fields in ResourceItem: {item}")
        elif isinstance(item, SubtitleGroupItem):
            if not item.get("id") or not item.get("name"):
                raise DropItem(f"Missing required fields in SubtitleGroupItem: {item}")
        elif isinstance(item, AnimeSubtitleGroupItem):
            if not item.get("mikan_id") or not item.get("subtitle_group_id"):
                raise DropItem(f"Missing required fields in AnimeSubtitleGroupItem: {item}")

        return item


class SQLitePipeline:
    """SQLite数据库Pipeline - 使用读写分离架构"""

    def __init__(self):
        self.db_manager = None

    def open_spider(self, spider):
        """初始化数据库管理器"""
        try:
            self.db_manager = DatabaseManager()
            spider.logger.info("✅ 数据库管理器已初始化（读写分离模式）")

            # 创建表结构
            self.create_tables()

        except Exception as e:
            spider.logger.error(f"数据库初始化失败: {e}")
            raise e

    def close_spider(self, spider):
        """关闭数据库连接"""
        if self.db_manager:
            try:
                self.db_manager.close_all()
                spider.logger.info("✅ 数据库连接已关闭")
            except Exception as e:
                spider.logger.error(f"关闭数据库连接失败: {e}")

    def create_tables(self):
        """创建优化后的数据库表结构"""
        if not self.db_manager:
            return

        # 使用写连接创建表
        with self.db_manager.write_manager.get_write_connection() as conn:
            cursor = conn.cursor()

            # 启用外键约束并验证
            cursor.execute("PRAGMA foreign_keys = ON")
            fk_status = cursor.execute("PRAGMA foreign_keys").fetchone()[0]
            if fk_status == 1:
                print("✅ 外键约束已成功启用")
            else:
                print("⚠️  外键约束启用失败")

            # 1. 创建动画表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS animes (
                    mikan_id INTEGER PRIMARY KEY,
                    bangumi_id INTEGER,
                    title TEXT NOT NULL,
                    original_title TEXT,
                    broadcast_day TEXT,
                    broadcast_start INTEGER,
                    official_website TEXT,
                    bangumi_url TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'unknown',
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            """)

            # 2. 创建字幕组表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subtitle_groups (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    last_update INTEGER,
                    created_at INTEGER NOT NULL
                )
            """)

            # 3. 创建动画-字幕组关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anime_subtitle_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mikan_id INTEGER NOT NULL,
                    subtitle_group_id INTEGER NOT NULL,
                    first_release_date INTEGER,
                    last_update_date INTEGER,
                    resource_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (mikan_id) REFERENCES animes (mikan_id) ON DELETE CASCADE,
                    FOREIGN KEY (subtitle_group_id) REFERENCES subtitle_groups (id) ON DELETE CASCADE,
                    UNIQUE (mikan_id, subtitle_group_id)
                )
            """)

            # 4. 创建资源表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mikan_id INTEGER NOT NULL,
                    subtitle_group_id INTEGER NOT NULL,
                    episode_number INTEGER,
                    title TEXT NOT NULL,
                    file_size TEXT,
                    resolution TEXT,
                    subtitle_type TEXT,
                    magnet_url TEXT,
                    torrent_url TEXT,
                    play_url TEXT,
                    magnet_hash TEXT,
                    release_date INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (mikan_id) REFERENCES animes (mikan_id) ON DELETE CASCADE,
                    FOREIGN KEY (subtitle_group_id) REFERENCES subtitle_groups (id) ON DELETE CASCADE,
                    UNIQUE (mikan_id, subtitle_group_id, magnet_hash)
                )
            """)

            # 5. 创建爬取日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawl_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spider_name TEXT NOT NULL,
                    start_time INTEGER,
                    end_time INTEGER,
                    status TEXT,
                    items_count INTEGER DEFAULT 0,
                    mikan_id INTEGER,
                    error_message TEXT,
                    created_at INTEGER NOT NULL
                )
            """)

            # 6. 创建索引
            self._create_indexes(cursor)

            conn.commit()

    def _create_indexes(self, cursor):
        """创建优化索引"""
        # anime_subtitle_groups表索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anime_subtitle_groups_mikan_id
            ON anime_subtitle_groups(mikan_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anime_subtitle_groups_subtitle_group_id
            ON anime_subtitle_groups(subtitle_group_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anime_subtitle_groups_last_update
            ON anime_subtitle_groups(last_update_date)
        """)

        # animes表索引 (重要：bangumi_id查询优化)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_animes_bangumi_id
            ON animes(bangumi_id)
        """)

        # resources表索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resources_mikan_id_created_at
            ON resources(mikan_id, created_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resources_release_date
            ON resources(release_date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resources_episode_number
            ON resources(mikan_id, episode_number)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resources_resolution
            ON resources(resolution)
        """)

    def process_item(self, item, spider):
        """处理数据项 - 使用写连接"""
        if not self.db_manager:
            return item

        try:
            if isinstance(item, AnimeItem):
                self.save_anime(item)
            elif isinstance(item, SubtitleGroupItem):
                self.save_subtitle_group(item)
            elif isinstance(item, AnimeSubtitleGroupItem):
                self.save_anime_subtitle_group(item)
            elif isinstance(item, ResourceItem):
                self.save_resource(item)
            elif isinstance(item, CrawlLogItem):
                self.save_crawl_log(item)
        except Exception as e:
            spider.logger.error(f"Error saving item to database: {e}")
            raise DropItem(f"Database error: {e}")

        return item

    def save_anime(self, item):
        """保存动画信息 - 使用写连接"""
        if not self.db_manager:
            return

        query = """
        INSERT OR REPLACE INTO animes 
        (mikan_id, bangumi_id, title, original_title, broadcast_day, broadcast_start,
         official_website, bangumi_url, description, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            item.get("mikan_id"),
            item.get("bangumi_id"),
            item.get("title"),
            item.get("original_title"),
            item.get("broadcast_day"),
            item.get("broadcast_start"),
            item.get("official_website"),
            item.get("bangumi_url"),
            item.get("description"),
            item.get("status", "unknown"),
            item.get("created_at"),
            item.get("updated_at"),
        )

        self.db_manager.execute_update(query, params)

    def save_subtitle_group(self, item):
        """保存字幕组信息 - 使用写连接"""
        if not self.db_manager:
            return

        query = """
        INSERT OR REPLACE INTO subtitle_groups 
        (id, name, last_update, created_at)
        VALUES (?, ?, ?, ?)
        """
        params = (
            item.get("id"),
            item.get("name"),
            item.get("last_update"),
            item.get("created_at"),
        )

        self.db_manager.execute_update(query, params)

    def save_anime_subtitle_group(self, item):
        """保存动画-字幕组关联信息 - 使用写连接"""
        if not self.db_manager:
            return

        query = """
        INSERT OR REPLACE INTO anime_subtitle_groups 
        (mikan_id, subtitle_group_id, first_release_date, last_update_date,
         resource_count, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            item.get("mikan_id"),
            item.get("subtitle_group_id"),
            item.get("first_release_date"),
            item.get("last_update_date"),
            item.get("resource_count", 0),
            item.get("is_active", 1),
            item.get("created_at"),
            item.get("updated_at"),
        )

        self.db_manager.execute_update(query, params)

    def save_resource(self, item):
        """保存资源信息 - 使用写连接"""
        if not self.db_manager:
            return

        query = """
        INSERT OR REPLACE INTO resources 
        (mikan_id, subtitle_group_id, episode_number, title, file_size,
         resolution, subtitle_type, magnet_url, torrent_url, play_url,
         magnet_hash, release_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            item.get("mikan_id"),
            item.get("subtitle_group_id"),
            item.get("episode_number"),
            item.get("title"),
            item.get("file_size"),
            item.get("resolution"),
            item.get("subtitle_type"),
            item.get("magnet_url"),
            item.get("torrent_url"),
            item.get("play_url"),
            item.get("magnet_hash"),
            item.get("release_date"),
            item.get("created_at"),
            item.get("updated_at"),
        )

        self.db_manager.execute_update(query, params)

    def save_crawl_log(self, item):
        """保存爬取日志 - 使用写连接"""
        if not self.db_manager:
            return

        query = """
        INSERT INTO crawl_logs 
        (spider_name, start_time, end_time, status, items_count, mikan_id,
         error_message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            item.get("spider_name"),
            item.get("start_time"),
            item.get("end_time"),
            item.get("status"),
            item.get("items_count", 0),
            item.get("mikan_id"),
            item.get("error_message"),
            item.get("created_at"),
        )

        self.db_manager.execute_update(query, params)


class DuplicatesPipeline:
    """去重Pipeline - 适配新结构"""

    def __init__(self):
        self.anime_ids = set()
        self.subtitle_group_ids = set()
        self.resource_hashes = set()
        self.anime_subtitle_group_pairs = set()

    def process_item(self, item, spider):
        if isinstance(item, AnimeItem):
            mikan_id = item.get("mikan_id")
            if mikan_id in self.anime_ids:
                raise DropItem(f"Duplicate anime: {mikan_id}")
            self.anime_ids.add(mikan_id)

        elif isinstance(item, SubtitleGroupItem):
            group_id = item.get("id")
            if group_id in self.subtitle_group_ids:
                raise DropItem(f"Duplicate subtitle group: {group_id}")
            self.subtitle_group_ids.add(group_id)

        elif isinstance(item, AnimeSubtitleGroupItem):
            mikan_id = item.get("mikan_id")
            subtitle_group_id = item.get("subtitle_group_id")
            pair = (mikan_id, subtitle_group_id)
            if pair in self.anime_subtitle_group_pairs:
                raise DropItem(f"Duplicate anime-subtitle group pair: {pair}")
            self.anime_subtitle_group_pairs.add(pair)

        elif isinstance(item, ResourceItem):
            magnet_hash = item.get("magnet_hash")
            if magnet_hash and magnet_hash in self.resource_hashes:
                raise DropItem(f"Duplicate resource: {magnet_hash}")
            if magnet_hash:
                self.resource_hashes.add(magnet_hash)

        return item
