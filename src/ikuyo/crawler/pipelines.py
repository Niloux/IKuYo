#!/usr/bin/env python3
"""
数据处理管道
负责将爬取的数据保存到数据库
"""

import json
import sqlite3
from datetime import datetime

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from src.ikuyo.config import get_config

from .items import AnimeItem, CrawlLogItem, ResourceItem, SubtitleGroupItem


class IkuyoScrapyPipeline:
    def process_item(self, item, spider):
        return item


class JsonWriterPipeline:
    """JSON输出Pipeline"""

    def open_spider(self, spider):
        self.file = open(
            f"output/anime_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json",
            "w",
            encoding="utf-8",
        )
        self.file.write("[\n")
        self.first_item = True

    def close_spider(self, spider):
        self.file.write("\n]")
        self.file.close()

    def process_item(self, item, spider):
        if not self.first_item:
            self.file.write(",\n")
        line = json.dumps(dict(item), ensure_ascii=False, indent=2)
        self.file.write(line)
        self.first_item = False
        return item


class DataValidationPipeline:
    """数据验证Pipeline"""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 验证必要字段
        if hasattr(item, "mikan_id") and not adapter.get("mikan_id"):
            spider.logger.warning(f"缺少mikan_id: {item}")

        if hasattr(item, "title") and not adapter.get("title"):
            spider.logger.warning(f"缺少title: {item}")

        return item


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

        return item


class SQLitePipeline:
    """SQLite数据库Pipeline"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def open_spider(self, spider):
        """打开数据库连接"""
        db_path = get_config("database", "sqlite_db")
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        if self.cursor:
            self.create_tables()

    def close_spider(self, spider):
        """关闭数据库连接"""
        if self.conn:
            if self.cursor:
                self.conn.commit()
            self.conn.close()

    def create_tables(self):
        """创建数据库表"""
        if not self.cursor:
            return

        # 动画表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS animes (
                mikan_id INTEGER PRIMARY KEY,
                bangumi_id INTEGER,
                title TEXT NOT NULL,
                original_title TEXT,
                broadcast_day TEXT,
                broadcast_start TEXT,
                official_website TEXT,
                bangumi_url TEXT,
                description TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # 字幕组表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subtitle_groups (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                last_update TEXT,
                is_subscribed INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)

        # 资源表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mikan_id INTEGER NOT NULL,
                subtitle_group_id INTEGER NOT NULL,
                episode_number INTEGER,
                title TEXT NOT NULL,
                file_size TEXT,
                magnet_url TEXT,
                torrent_url TEXT,
                play_url TEXT,
                magnet_hash TEXT,
                release_date TEXT,
                created_at TEXT,
                FOREIGN KEY (mikan_id) REFERENCES animes (mikan_id),
                FOREIGN KEY (subtitle_group_id) REFERENCES subtitle_groups (id),
                UNIQUE (mikan_id, subtitle_group_id, magnet_hash)
            )
        """)

        # 爬取日志表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spider_name TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                status TEXT,
                items_count INTEGER DEFAULT 0,
                mikan_id INTEGER,
                error_message TEXT,
                created_at TEXT
            )
        """)

        if self.conn:
            self.conn.commit()

    def process_item(self, item, spider):
        """处理数据项"""
        if not self.cursor:
            return item

        try:
            if isinstance(item, AnimeItem):
                self.save_anime(item)
            elif isinstance(item, SubtitleGroupItem):
                self.save_subtitle_group(item)
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

    def save_resource(self, item):
        """保存资源信息"""
        if not self.cursor:
            return

        self.cursor.execute(
            """
            INSERT OR IGNORE INTO resources
            (mikan_id, subtitle_group_id, episode_number, title, file_size,
             magnet_url, torrent_url, play_url, magnet_hash, release_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                item.get("mikan_id"),
                item.get("subtitle_group_id"),
                item.get("episode_number"),
                item.get("title"),
                item.get("file_size"),
                item.get("magnet_url"),
                item.get("torrent_url"),
                item.get("play_url"),
                item.get("magnet_hash"),
                item.get("release_date"),
                item.get("created_at"),
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
    """去重Pipeline"""

    def __init__(self):
        self.anime_ids = set()
        self.subtitle_group_ids = set()
        self.resource_hashes = set()

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

        elif isinstance(item, ResourceItem):
            magnet_hash = item.get("magnet_hash")
            if magnet_hash and magnet_hash in self.resource_hashes:
                raise DropItem(f"Duplicate resource: {magnet_hash}")
            if magnet_hash:
                self.resource_hashes.add(magnet_hash)

        return item
