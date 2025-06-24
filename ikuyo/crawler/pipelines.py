#!/usr/bin/env python3
"""
数据处理管道
负责将爬取的数据保存到数据库
"""

import sqlite3

from scrapy.exceptions import DropItem

from ..core.config import load_config
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
    """SQLite数据库Pipeline"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def open_spider(self, spider):
        """打开数据库连接并启用外键约束"""
        config = load_config()
        db_path = getattr(config.database, "path", "data/database/ikuyo.db")
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # 启用外键约束并验证
        self.cursor.execute("PRAGMA foreign_keys = ON")
        fk_status = self.cursor.execute("PRAGMA foreign_keys").fetchone()[0]
        if fk_status == 1:
            spider.logger.info("✅ 外键约束已成功启用")
        else:
            spider.logger.warning("⚠️  外键约束启用失败")

        if self.cursor:
            self.create_tables()

    def close_spider(self, spider):
        """关闭数据库连接"""
        if self.conn:
            if self.cursor:
                self.conn.commit()
            self.conn.close()

    def create_tables(self):
        """创建优化后的数据库表结构"""
        if not self.cursor:
            return

        # 1. 创建动画表
        self.cursor.execute("""
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
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subtitle_groups (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                last_update INTEGER,
                is_subscribed INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL
            )
        """)

        # 3. 创建动画-字幕组关联表
        self.cursor.execute("""
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
        self.cursor.execute("""
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
        self.cursor.execute("""
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
        self._create_indexes()

        if self.conn:
            self.conn.commit()

    def _create_indexes(self):
        """创建优化索引"""
        if not self.cursor:
            return

            # anime_subtitle_groups表索引
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anime_subtitle_groups_mikan_id
            ON anime_subtitle_groups(mikan_id)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anime_subtitle_groups_subtitle_group_id
            ON anime_subtitle_groups(subtitle_group_id)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anime_subtitle_groups_last_update
            ON anime_subtitle_groups(last_update_date)
        """)

        # resources表索引
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resources_mikan_id_created_at
            ON resources(mikan_id, created_at)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resources_release_date
            ON resources(release_date)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resources_episode_number
            ON resources(mikan_id, episode_number)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resources_resolution
            ON resources(resolution)
        """)

    def process_item(self, item, spider):
        """处理数据项"""
        if not self.cursor:
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
        """保存动画信息"""
        if not self.cursor:
            return

        self.cursor.execute(
            """
            INSERT OR REPLACE INTO animes
            (mikan_id, bangumi_id, title, original_title, broadcast_day,
             broadcast_start, official_website, bangumi_url, description,
             status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                item.get("mikan_id"),
                item.get("bangumi_id"),
                item.get("title"),
                item.get("original_title"),
                item.get("broadcast_day"),
                item.get("broadcast_start"),
                item.get("official_website"),
                item.get("bangumi_url"),
                item.get("description"),
                item.get("status"),
                item.get("created_at"),
                item.get("updated_at"),
            ),
        )

    def save_subtitle_group(self, item):
        """保存字幕组信息"""
        if not self.cursor:
            return

        self.cursor.execute(
            """
            INSERT OR REPLACE INTO subtitle_groups
            (id, name, last_update, is_subscribed, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                item.get("id"),
                item.get("name"),
                item.get("last_update"),
                item.get("is_subscribed", 0),
                item.get("created_at"),
            ),
        )

    def save_anime_subtitle_group(self, item):
        """保存动画-字幕组关联信息"""
        if not self.cursor:
            return

        self.cursor.execute(
            """
            INSERT INTO anime_subtitle_groups
            (mikan_id, subtitle_group_id, first_release_date, last_update_date,
             resource_count, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(mikan_id, subtitle_group_id)
            DO UPDATE SET
                last_update_date = excluded.last_update_date,
                resource_count = excluded.resource_count,
                is_active = excluded.is_active,
                updated_at = excluded.updated_at
        """,
            (
                item.get("mikan_id"),
                item.get("subtitle_group_id"),
                item.get("first_release_date"),
                item.get("last_update_date"),
                item.get("resource_count"),
                item.get("is_active", 1),
                item.get("created_at"),
                item.get("updated_at"),
            ),
        )

    def save_resource(self, item):
        """保存资源信息 - 使用UPSERT机制"""
        if not self.cursor:
            return

        self.cursor.execute(
            """
            INSERT INTO resources
            (mikan_id, subtitle_group_id, episode_number, title, file_size,
             resolution, subtitle_type, magnet_url, torrent_url, play_url,
             magnet_hash, release_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(mikan_id, subtitle_group_id, magnet_hash)
            DO UPDATE SET
                title = excluded.title,
                episode_number = excluded.episode_number,
                resolution = excluded.resolution,
                subtitle_type = excluded.subtitle_type,
                file_size = excluded.file_size,
                updated_at = excluded.updated_at
        """,
            (
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
            ),
        )

    def save_crawl_log(self, item):
        """保存爬取日志"""
        if not self.cursor:
            return

        self.cursor.execute(
            """
            INSERT INTO crawl_logs
            (spider_name, start_time, end_time, status, items_count,
             mikan_id, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                item.get("spider_name"),
                item.get("start_time"),
                item.get("end_time"),
                item.get("status"),
                item.get("items_count"),
                item.get("mikan_id"),
                item.get("error_message"),
                item.get("created_at"),
            ),
        )


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
