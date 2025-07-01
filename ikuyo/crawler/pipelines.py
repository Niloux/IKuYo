#!/usr/bin/env python3
"""
数据处理管道
负责将爬取的数据保存到数据库
更新以支持读写分离架构
"""

from scrapy.exceptions import DropItem
from ikuyo.core.database import get_session
from ikuyo.core.repositories import (
    AnimeRepository,
    SubtitleGroupRepository,
    AnimeSubtitleGroupRepository,
    ResourceRepository,
    CrawlLogRepository,
)
from ikuyo.core.models import Anime, SubtitleGroup, AnimeSubtitleGroup, Resource, CrawlLog
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
    """SQLite数据库Pipeline - 使用Repository模式"""

    def __init__(self):
        self.session = None
        self.anime_repo = None
        self.subtitle_group_repo = None
        self.anime_subtitle_group_repo = None
        self.resource_repo = None
        self.crawl_log_repo = None

    def open_spider(self, spider):
        try:
            self.session = get_session()
            self.anime_repo = AnimeRepository(self.session)
            self.subtitle_group_repo = SubtitleGroupRepository(self.session)
            self.anime_subtitle_group_repo = AnimeSubtitleGroupRepository(self.session)
            self.resource_repo = ResourceRepository(self.session)
            self.crawl_log_repo = CrawlLogRepository(self.session)
            spider.logger.info("✅ 数据库Repository已初始化")
        except Exception as e:
            spider.logger.error(f"数据库初始化失败: {e}")
            raise e

    def close_spider(self, spider):
        if self.session:
            try:
                self.session.close()
                spider.logger.info("✅ 数据库Session已关闭")
            except Exception as e:
                spider.logger.error(f"关闭数据库Session失败: {e}")

    def process_item(self, item, spider):
        if not self.session:
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
        if self.anime_repo:
            obj = Anime(**item)
            self.anime_repo.create(obj)

    def save_subtitle_group(self, item):
        if self.subtitle_group_repo:
            obj = SubtitleGroup(**item)
            self.subtitle_group_repo.create(obj)

    def save_anime_subtitle_group(self, item):
        if self.anime_subtitle_group_repo:
            obj = AnimeSubtitleGroup(**item)
            self.anime_subtitle_group_repo.create(obj)

    def save_resource(self, item):
        if self.resource_repo:
            obj = Resource(**item)
            self.resource_repo.create(obj)

    def save_crawl_log(self, item):
        if self.crawl_log_repo:
            obj = CrawlLog(**item)
            self.crawl_log_repo.create(obj)


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


class BatchSQLitePipeline:
    """批量存储Pipeline - 使用Repository模式"""

    def __init__(self):
        self.session = None
        self.anime_repo = None
        self.subtitle_group_repo = None
        self.anime_subtitle_group_repo = None
        self.resource_repo = None
        self.crawl_log_repo = None
        self.batch_size = 100  # 简单固定值，不搞复杂配置
        self.batches = {
            "animes": [],
            "subtitle_groups": [],
            "anime_subtitle_groups": [],
            "resources": [],
            "crawl_logs": [],
        }

    def open_spider(self, spider):
        try:
            self.session = get_session()
            self.anime_repo = AnimeRepository(self.session)
            self.subtitle_group_repo = SubtitleGroupRepository(self.session)
            self.anime_subtitle_group_repo = AnimeSubtitleGroupRepository(self.session)
            self.resource_repo = ResourceRepository(self.session)
            self.crawl_log_repo = CrawlLogRepository(self.session)
            spider.logger.info("✅ 批量存储Pipeline已初始化")
        except Exception as e:
            spider.logger.error(f"批量Pipeline初始化失败: {e}")
            raise e

    def close_spider(self, spider):
        if self.session:
            try:
                self._flush_all_batches(spider)
                self.session.close()
                spider.logger.info("✅ 批量存储Pipeline已关闭")
            except Exception as e:
                spider.logger.error(f"关闭批量Pipeline失败: {e}")

    def process_item(self, item, spider):
        if not self.session:
            return item
        try:
            if isinstance(item, AnimeItem):
                self.batches["animes"].append(item)
                if len(self.batches["animes"]) >= self.batch_size:
                    self._flush_animes(spider)
            elif isinstance(item, SubtitleGroupItem):
                self.batches["subtitle_groups"].append(item)
                if len(self.batches["subtitle_groups"]) >= self.batch_size:
                    self._flush_subtitle_groups(spider)
            elif isinstance(item, AnimeSubtitleGroupItem):
                self.batches["anime_subtitle_groups"].append(item)
                if len(self.batches["anime_subtitle_groups"]) >= self.batch_size:
                    self._flush_dependencies_first(spider)
                    self._flush_anime_subtitle_groups(spider)
            elif isinstance(item, ResourceItem):
                self.batches["resources"].append(item)
                if len(self.batches["resources"]) >= self.batch_size:
                    self._flush_dependencies_first(spider)
                    self._flush_resources(spider)
            elif isinstance(item, CrawlLogItem):
                self.batches["crawl_logs"].append(item)
                if len(self.batches["crawl_logs"]) >= self.batch_size:
                    self._flush_crawl_logs(spider)
        except Exception as e:
            spider.logger.error(f"批量处理item失败: {e}")
            raise DropItem(f"Batch processing error: {e}")
        return item

    def _flush_dependencies_first(self, spider):
        if self.batches["animes"]:
            self._flush_animes(spider)
        if self.batches["subtitle_groups"]:
            self._flush_subtitle_groups(spider)

    def _flush_animes(self, spider):
        if not self.batches["animes"] or not self.anime_repo:
            return
        try:
            for item in self.batches["animes"]:
                self.anime_repo.create(Anime(**item))
            spider.logger.info(f"✅ 批量插入动画: {len(self.batches['animes'])} 条")
        except Exception as e:
            spider.logger.error(f"批量插入动画失败: {e}")
        finally:
            self.batches["animes"].clear()

    def _flush_subtitle_groups(self, spider):
        if not self.batches["subtitle_groups"] or not self.subtitle_group_repo:
            return
        try:
            for item in self.batches["subtitle_groups"]:
                self.subtitle_group_repo.create(SubtitleGroup(**item))
            spider.logger.info(f"✅ 批量插入字幕组: {len(self.batches['subtitle_groups'])} 条")
        except Exception as e:
            spider.logger.error(f"批量插入字幕组失败: {e}")
        finally:
            self.batches["subtitle_groups"].clear()

    def _flush_anime_subtitle_groups(self, spider):
        if not self.batches["anime_subtitle_groups"] or not self.anime_subtitle_group_repo:
            return
        try:
            for item in self.batches["anime_subtitle_groups"]:
                self.anime_subtitle_group_repo.create(AnimeSubtitleGroup(**item))
            spider.logger.info(
                f"✅ 批量插入动画-字幕组关联: {len(self.batches['anime_subtitle_groups'])} 条"
            )
        except Exception as e:
            spider.logger.error(f"批量插入关联数据失败: {e}")
        finally:
            self.batches["anime_subtitle_groups"].clear()

    def _flush_resources(self, spider):
        if not self.batches["resources"] or not self.resource_repo:
            return
        try:
            for item in self.batches["resources"]:
                self.resource_repo.create(Resource(**item))
            spider.logger.info(f"✅ 批量插入资源: {len(self.batches['resources'])} 条")
        except Exception as e:
            spider.logger.error(f"批量插入资源失败: {e}")
        finally:
            self.batches["resources"].clear()

    def _flush_crawl_logs(self, spider):
        if not self.batches["crawl_logs"] or not self.crawl_log_repo:
            return
        try:
            for item in self.batches["crawl_logs"]:
                self.crawl_log_repo.create(CrawlLog(**item))
            spider.logger.info(f"✅ 批量插入日志: {len(self.batches['crawl_logs'])} 条")
        except Exception as e:
            spider.logger.error(f"批量插入日志失败: {e}")
        finally:
            self.batches["crawl_logs"].clear()

    def _flush_all_batches(self, spider):
        spider.logger.info("🔄 刷新所有缓存批次...")
        self._flush_animes(spider)
        self._flush_subtitle_groups(spider)
        self._flush_anime_subtitle_groups(spider)
        self._flush_resources(spider)
        self._flush_crawl_logs(spider)
        spider.logger.info("✅ 所有批次刷新完成")
