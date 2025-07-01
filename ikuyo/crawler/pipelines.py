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


class BatchSQLitePipeline:
    """批量存储Pipeline - 减少数据库写操作次数"""

    def __init__(self):
        self.db_manager = None
        self.batch_size = 100  # 简单固定值，不搞复杂配置

        # 分类缓存不同类型的items
        self.batches = {
            "animes": [],
            "subtitle_groups": [],
            "anime_subtitle_groups": [],
            "resources": [],
            "crawl_logs": [],
        }

    def open_spider(self, spider):
        """初始化数据库管理器"""
        try:
            self.db_manager = DatabaseManager()
            spider.logger.info("✅ 批量存储Pipeline已初始化")

        except Exception as e:
            spider.logger.error(f"批量Pipeline初始化失败: {e}")
            raise e

    def close_spider(self, spider):
        """爬虫结束时刷新所有缓存"""
        if self.db_manager:
            try:
                # 刷新所有缓存的数据
                self._flush_all_batches(spider)
                self.db_manager.close_all()
                spider.logger.info("✅ 批量存储Pipeline已关闭")
            except Exception as e:
                spider.logger.error(f"关闭批量Pipeline失败: {e}")

    def process_item(self, item, spider):
        """缓存item，达到阈值时批量写入"""
        if not self.db_manager:
            return item

        try:
            # 根据item类型缓存到对应的批次中
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
                    # 先刷新依赖项，再刷新当前项
                    self._flush_dependencies_first(spider)
                    self._flush_anime_subtitle_groups(spider)

            elif isinstance(item, ResourceItem):
                self.batches["resources"].append(item)
                if len(self.batches["resources"]) >= self.batch_size:
                    # 先刷新依赖项，再刷新当前项
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
        """优先刷新依赖项（animes和subtitle_groups）"""
        if self.batches["animes"]:
            self._flush_animes(spider)
        if self.batches["subtitle_groups"]:
            self._flush_subtitle_groups(spider)

    def _flush_animes(self, spider):
        """批量插入动画数据"""
        if not self.batches["animes"]:
            return

        # 类型检查 - 确保db_manager和write_manager存在
        if not self.db_manager or not hasattr(self.db_manager, "write_manager"):
            spider.logger.error("数据库管理器未正确初始化")
            return

        try:
            with self.db_manager.write_manager.get_write_connection() as conn:
                cursor = conn.cursor()

                data = []
                for item in self.batches["animes"]:
                    data.append((
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
                    ))

                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO animes 
                    (mikan_id, bangumi_id, title, original_title, broadcast_day, broadcast_start,
                     official_website, bangumi_url, description, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    data,
                )

                conn.commit()
                spider.logger.info(f"✅ 批量插入动画: {len(data)} 条")

        except Exception as e:
            spider.logger.error(f"批量插入动画失败: {e}")
            # 降级为单条插入
            self._fallback_insert_animes(spider)

        finally:
            self.batches["animes"].clear()

    def _flush_subtitle_groups(self, spider):
        """批量插入字幕组数据"""
        if not self.batches["subtitle_groups"]:
            return

        # 类型检查 - 确保db_manager和write_manager存在
        if not self.db_manager or not hasattr(self.db_manager, "write_manager"):
            spider.logger.error("数据库管理器未正确初始化")
            return

        try:
            with self.db_manager.write_manager.get_write_connection() as conn:
                cursor = conn.cursor()

                data = []
                for item in self.batches["subtitle_groups"]:
                    data.append((
                        item.get("id"),
                        item.get("name"),
                        item.get("last_update"),
                        item.get("created_at"),
                    ))

                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO subtitle_groups 
                    (id, name, last_update, created_at)
                    VALUES (?, ?, ?, ?)
                """,
                    data,
                )

                conn.commit()
                spider.logger.info(f"✅ 批量插入字幕组: {len(data)} 条")

        except Exception as e:
            spider.logger.error(f"批量插入字幕组失败: {e}")
            self._fallback_insert_subtitle_groups(spider)

        finally:
            self.batches["subtitle_groups"].clear()

    def _flush_anime_subtitle_groups(self, spider):
        """批量插入动画-字幕组关联数据"""
        if not self.batches["anime_subtitle_groups"]:
            return

        # 类型检查 - 确保db_manager和write_manager存在
        if not self.db_manager or not hasattr(self.db_manager, "write_manager"):
            spider.logger.error("数据库管理器未正确初始化")
            return

        try:
            with self.db_manager.write_manager.get_write_connection() as conn:
                cursor = conn.cursor()

                data = []
                for item in self.batches["anime_subtitle_groups"]:
                    data.append((
                        item.get("mikan_id"),
                        item.get("subtitle_group_id"),
                        item.get("first_release_date"),
                        item.get("last_update_date"),
                        item.get("resource_count", 0),
                        item.get("is_active", 1),
                        item.get("created_at"),
                        item.get("updated_at"),
                    ))

                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO anime_subtitle_groups 
                    (mikan_id, subtitle_group_id, first_release_date, last_update_date,
                     resource_count, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    data,
                )

                conn.commit()
                spider.logger.info(f"✅ 批量插入动画-字幕组关联: {len(data)} 条")

        except Exception as e:
            spider.logger.error(f"批量插入关联数据失败: {e}")
            # 降级前先确保依赖项存在
            self._ensure_dependencies_exist(spider)
            self._fallback_insert_anime_subtitle_groups(spider)

        finally:
            self.batches["anime_subtitle_groups"].clear()

    def _flush_resources(self, spider):
        """批量插入资源数据"""
        if not self.batches["resources"]:
            return

        # 类型检查 - 确保db_manager和write_manager存在
        if not self.db_manager or not hasattr(self.db_manager, "write_manager"):
            spider.logger.error("数据库管理器未正确初始化")
            return

        try:
            with self.db_manager.write_manager.get_write_connection() as conn:
                cursor = conn.cursor()

                data = []
                for item in self.batches["resources"]:
                    data.append((
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
                    ))

                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO resources 
                    (mikan_id, subtitle_group_id, episode_number, title, file_size,
                     resolution, subtitle_type, magnet_url, torrent_url, play_url,
                     magnet_hash, release_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    data,
                )

                conn.commit()
                spider.logger.info(f"✅ 批量插入资源: {len(data)} 条")

        except Exception as e:
            spider.logger.error(f"批量插入资源失败: {e}")
            # 降级前先确保依赖项存在
            self._ensure_dependencies_exist(spider)
            self._fallback_insert_resources(spider)

        finally:
            self.batches["resources"].clear()

    def _flush_crawl_logs(self, spider):
        """批量插入爬取日志"""
        if not self.batches["crawl_logs"]:
            return

        # 类型检查 - 确保db_manager和write_manager存在
        if not self.db_manager or not hasattr(self.db_manager, "write_manager"):
            spider.logger.error("数据库管理器未正确初始化")
            return

        try:
            with self.db_manager.write_manager.get_write_connection() as conn:
                cursor = conn.cursor()

                data = []
                for item in self.batches["crawl_logs"]:
                    data.append((
                        item.get("spider_name"),
                        item.get("start_time"),
                        item.get("end_time"),
                        item.get("status"),
                        item.get("items_count", 0),
                        item.get("mikan_id"),
                        item.get("error_message"),
                        item.get("created_at"),
                    ))

                cursor.executemany(
                    """
                    INSERT INTO crawl_logs 
                    (spider_name, start_time, end_time, status, items_count, mikan_id,
                     error_message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    data,
                )

                conn.commit()
                spider.logger.info(f"✅ 批量插入日志: {len(data)} 条")

        except Exception as e:
            spider.logger.error(f"批量插入日志失败: {e}")

        finally:
            self.batches["crawl_logs"].clear()

    def _flush_all_batches(self, spider):
        """刷新所有缓存的批次"""
        spider.logger.info("🔄 刷新所有缓存批次...")

        self._flush_animes(spider)
        self._flush_subtitle_groups(spider)
        self._flush_anime_subtitle_groups(spider)
        self._flush_resources(spider)
        self._flush_crawl_logs(spider)

        spider.logger.info("✅ 所有批次刷新完成")

    def _fallback_insert_animes(self, spider):
        """降级为单条插入动画（失败时使用）"""
        spider.logger.warning("🔄 降级为单条插入动画...")

        # 类型检查 - 确保db_manager和execute_update存在
        if not self.db_manager or not hasattr(self.db_manager, "execute_update"):
            spider.logger.error("数据库管理器未正确初始化")
            return

        for item in self.batches["animes"]:
            try:
                self.db_manager.execute_update(
                    """
                    INSERT OR REPLACE INTO animes 
                    (mikan_id, bangumi_id, title, original_title, broadcast_day, broadcast_start,
                     official_website, bangumi_url, description, status, created_at, updated_at)
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
                        item.get("status", "unknown"),
                        item.get("created_at"),
                        item.get("updated_at"),
                    ),
                )
            except Exception as e:
                spider.logger.error(f"单条插入动画失败: {e}")

    def _fallback_insert_subtitle_groups(self, spider):
        """降级为单条插入字幕组（失败时使用）"""
        spider.logger.warning("🔄 降级为单条插入字幕组...")

        # 类型检查 - 确保db_manager和execute_update存在
        if not self.db_manager or not hasattr(self.db_manager, "execute_update"):
            spider.logger.error("数据库管理器未正确初始化")
            return

        for item in self.batches["subtitle_groups"]:
            try:
                self.db_manager.execute_update(
                    """
                    INSERT OR REPLACE INTO subtitle_groups 
                    (id, name, last_update, created_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        item.get("id"),
                        item.get("name"),
                        item.get("last_update"),
                        item.get("created_at"),
                    ),
                )
            except Exception as e:
                spider.logger.error(f"单条插入字幕组失败: {e}")

    def _fallback_insert_anime_subtitle_groups(self, spider):
        """降级为单条插入关联数据（失败时使用）"""
        spider.logger.warning("🔄 降级为单条插入关联数据...")

        # 类型检查 - 确保db_manager和execute_update存在
        if not self.db_manager or not hasattr(self.db_manager, "execute_update"):
            spider.logger.error("数据库管理器未正确初始化")
            return

        for item in self.batches["anime_subtitle_groups"]:
            try:
                self.db_manager.execute_update(
                    """
                    INSERT OR REPLACE INTO anime_subtitle_groups 
                    (mikan_id, subtitle_group_id, first_release_date, last_update_date,
                     resource_count, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        item.get("mikan_id"),
                        item.get("subtitle_group_id"),
                        item.get("first_release_date"),
                        item.get("last_update_date"),
                        item.get("resource_count", 0),
                        item.get("is_active", 1),
                        item.get("created_at"),
                        item.get("updated_at"),
                    ),
                )
            except Exception as e:
                spider.logger.error(f"单条插入关联数据失败: {e}")

    def _fallback_insert_resources(self, spider):
        """降级为单条插入资源（失败时使用）"""
        spider.logger.warning("🔄 降级为单条插入资源...")

        # 类型检查 - 确保db_manager和execute_update存在
        if not self.db_manager or not hasattr(self.db_manager, "execute_update"):
            spider.logger.error("数据库管理器未正确初始化")
            return

        for item in self.batches["resources"]:
            try:
                self.db_manager.execute_update(
                    """
                    INSERT OR REPLACE INTO resources 
                    (mikan_id, subtitle_group_id, episode_number, title, file_size,
                     resolution, subtitle_type, magnet_url, torrent_url, play_url,
                     magnet_hash, release_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            except Exception as e:
                spider.logger.error(f"单条插入资源失败: {e}")

    def _ensure_dependencies_exist(self, spider):
        """确保依赖项存在，用于降级处理前"""
        spider.logger.info("🔄 确保依赖项存在...")

        # 先处理所有待处理的animes和subtitle_groups
        if self.batches["animes"]:
            spider.logger.info(f"先插入待处理的动画: {len(self.batches['animes'])} 条")
            self._flush_animes(spider)

        if self.batches["subtitle_groups"]:
            spider.logger.info(f"先插入待处理的字幕组: {len(self.batches['subtitle_groups'])} 条")
            self._flush_subtitle_groups(spider)
