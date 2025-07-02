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
from ikuyo.core.crawler.progress_reporter import report_progress, report_status, report_result
import time


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
    """批量存储Pipeline"""

    def __init__(self, batch_size=100):
        self.batch_size = batch_size
        self.anime_batch = []
        self.subtitle_groups_batch = []
        self.resources_batch = []
        self.anime_subtitle_groups_batch = []
        self.anime_repo = None
        self.subtitle_group_repo = None
        self.anime_subtitle_group_repo = None
        self.resource_repo = None
        self.total_items = 0
        self.processed_items = 0
        self.start_time = None

    def open_spider(self, spider):
        """打开爬虫时初始化"""
        session = get_session()
        self.anime_repo = AnimeRepository(session)
        self.subtitle_group_repo = SubtitleGroupRepository(session)
        self.anime_subtitle_group_repo = AnimeSubtitleGroupRepository(session)
        self.resource_repo = ResourceRepository(session)
        self.start_time = time.time()
        spider.logger.info("✅ 批量存储Pipeline已初始化")

    def close_spider(self, spider):
        """关闭爬虫时刷新所有批次"""
        spider.logger.info("🔄 刷新所有缓存批次...")
        try:
            self._flush_anime_batch(spider)
            self._flush_subtitle_groups_batch(spider)
            self._flush_anime_subtitle_groups_batch(spider)
            self._flush_resources_batch(spider)
            spider.logger.info("✅ 所有批次刷新完成")
        except Exception as e:
            spider.logger.error(f"刷新批次时发生错误: {str(e)}")
        finally:
            if self.anime_repo:
                self.anime_repo.session.close()
            spider.logger.info("✅ 批量存储Pipeline已关闭")

    def process_item(self, item, spider):
        """处理爬取项"""
        if isinstance(item, AnimeItem):
            self.anime_batch.append(item)
            if len(self.anime_batch) >= self.batch_size:
                self._flush_anime_batch(spider)
            # 只在处理动画时更新进度
            self.processed_items += 1
            if hasattr(spider, "task_id") and spider.task_id is not None:
                self._report_progress(spider)

        elif isinstance(item, SubtitleGroupItem):
            self.subtitle_groups_batch.append(item)
            if len(self.subtitle_groups_batch) >= self.batch_size:
                self._flush_subtitle_groups_batch(spider)

        elif isinstance(item, ResourceItem):
            self.resources_batch.append(item)
            if len(self.resources_batch) >= self.batch_size:
                self._flush_resources_batch(spider)

        elif isinstance(item, AnimeSubtitleGroupItem):
            self.anime_subtitle_groups_batch.append(item)
            if len(self.anime_subtitle_groups_batch) >= self.batch_size:
                self._flush_anime_subtitle_groups_batch(spider)

        return item

    def _flush_anime_batch(self, spider):
        """刷新动画批次"""
        if not self.anime_batch or not self.anime_repo:
            return

        try:
            # 转换为模型对象
            anime_models = []
            for item in self.anime_batch:
                anime = Anime(
                    mikan_id=item["mikan_id"],
                    bangumi_id=item.get("bangumi_id"),
                    title=item["title"],
                    original_title=item.get("original_title"),
                    broadcast_day=item.get("broadcast_day"),
                    broadcast_start=item.get("broadcast_start"),
                    official_website=item.get("official_website"),
                    bangumi_url=item.get("bangumi_url"),
                    description=item.get("description"),
                    status="active",
                )
                anime_models.append(anime)

            # 批量更新或插入
            for anime in anime_models:
                existing = self.anime_repo.get_by_id(anime.mikan_id)
                if existing:
                    # 更新现有记录
                    for key, value in anime.model_dump().items():
                        if value is not None:
                            setattr(existing, key, value)
                    self.anime_repo.update(existing)
                else:
                    # 插入新记录
                    self.anime_repo.create(anime)

            self.anime_batch.clear()

        except Exception as e:
            spider.logger.error(f"批量插入动画失败: {str(e)}")

    def _flush_subtitle_groups_batch(self, spider):
        """刷新字幕组批次"""
        if not self.subtitle_groups_batch or not self.subtitle_group_repo:
            return

        try:
            # 转换为模型对象
            subtitle_group_models = []
            for item in self.subtitle_groups_batch:
                subtitle_group = SubtitleGroup(
                    id=item["id"],
                    name=item["name"],
                )
                subtitle_group_models.append(subtitle_group)

            # 批量更新或插入
            for group in subtitle_group_models:
                existing = self.subtitle_group_repo.get_by_id(group.id)
                if existing:
                    # 更新现有记录
                    for key, value in group.model_dump().items():
                        if value is not None:
                            setattr(existing, key, value)
                    self.subtitle_group_repo.update(existing)
                else:
                    # 插入新记录
                    self.subtitle_group_repo.create(group)

            self.subtitle_groups_batch.clear()

        except Exception as e:
            spider.logger.error(f"批量插入字幕组失败: {str(e)}")

    def _flush_anime_subtitle_groups_batch(self, spider):
        """刷新动画-字幕组关联批次"""
        if not self.anime_subtitle_groups_batch or not self.anime_subtitle_group_repo:
            return

        try:
            # 转换为模型对象
            relation_models = []
            for item in self.anime_subtitle_groups_batch:
                relation = AnimeSubtitleGroup(
                    mikan_id=item["mikan_id"],
                    subtitle_group_id=item["subtitle_group_id"],
                )
                relation_models.append(relation)

            # 批量更新或插入
            for relation in relation_models:
                existing = self.anime_subtitle_group_repo.get_by_mikan_and_group(
                    relation.mikan_id, relation.subtitle_group_id
                )
                if not existing:
                    # 只插入不存在的关联
                    self.anime_subtitle_group_repo.create(relation)

            self.anime_subtitle_groups_batch.clear()

        except Exception as e:
            spider.logger.error(f"批量插入关联数据失败: {str(e)}")

    def _flush_resources_batch(self, spider):
        """刷新资源批次"""
        if not self.resources_batch or not self.resource_repo:
            return

        try:
            # 转换为模型对象
            resource_models = []
            for item in self.resources_batch:
                resource = Resource(
                    mikan_id=item["mikan_id"],
                    subtitle_group_id=item["subtitle_group_id"],
                    episode_number=item.get("episode_number"),
                    title=item["title"],
                    file_size=item.get("file_size"),
                    resolution=item.get("resolution"),
                    subtitle_type=item.get("subtitle_type"),
                    magnet_url=item.get("magnet_url"),
                    torrent_url=item.get("torrent_url"),
                    play_url=item.get("play_url"),
                    magnet_hash=item.get("magnet_hash"),
                    release_date=item.get("release_date"),
                )
                resource_models.append(resource)

            # 批量更新或插入
            for resource in resource_models:
                existing = self.resource_repo.get_by_id(resource.id) if resource.id else None
                if existing:
                    # 更新现有记录
                    for key, value in resource.model_dump().items():
                        if value is not None:
                            setattr(existing, key, value)
                    self.resource_repo.update(existing)
                else:
                    # 插入新记录
                    self.resource_repo.create(resource)

            self.resources_batch.clear()

        except Exception as e:
            spider.logger.error(f"批量插入资源失败: {str(e)}")

    def _report_progress(self, spider):
        """报告进度"""
        if not hasattr(spider, "task_id") or spider.task_id is None:
            return

        # 获取total_items
        total_items = getattr(spider, "total_items", 0)
        spider.logger.info(f"Pipeline中的total_items值: {total_items}")
        spider.logger.info(f"Pipeline中的processed_items值: {self.processed_items}")

        # 计算进度
        if self.start_time is None:
            spider.logger.warning("start_time为None，跳过进度计算")
            return

        elapsed_time = time.time() - self.start_time
        if total_items > 0 and elapsed_time > 0:
            percentage = (self.processed_items / total_items) * 100
            processing_speed = self.processed_items / elapsed_time
            remaining_items = total_items - self.processed_items
            estimated_remaining = remaining_items / processing_speed if processing_speed > 0 else None

            report_progress({
                "total_items": total_items,
                "processed_items": self.processed_items,
                "percentage": percentage,
                "processing_speed": processing_speed,
                "estimated_remaining": estimated_remaining,
            })
        else:
            spider.logger.warning("total_items或elapsed_time为0，跳过进度计算")


class ProgressReportPipeline:
    """进度报告管道"""

    def __init__(self):
        self.start_time = time.time()
        self.last_report_time = self.start_time

    def process_item(self, item, spider):
        """处理每个项目并更新进度"""
        if not hasattr(spider, "task_id") or spider.task_id is None:
            return item

        # 只有处理 AnimeItem 时才更新进度
        if isinstance(item, AnimeItem):
            current_time = time.time()
            time_since_last_report = current_time - self.last_report_time

            # 每秒最多更新一次进度
            if time_since_last_report >= 1.0:
                self.last_report_time = current_time
                elapsed_time = current_time - self.start_time

                spider.logger.info(f"Pipeline中的total_items值: {spider.total_items}")  # 添加日志
                spider.logger.info(f"Pipeline中的processed_items值: {spider.processed_items}")  # 添加日志

                # 基本的除零保护
                if spider.total_items == 0 or elapsed_time == 0:
                    spider.logger.warning("total_items或elapsed_time为0，跳过进度计算")  # 添加日志
                    return item

                # 计算进度
                percentage = (spider.processed_items / spider.total_items) * 100
                processing_speed = (spider.processed_items / elapsed_time) * 60  # 每分钟处理数量
                remaining_items = spider.total_items - spider.processed_items
                estimated_remaining = remaining_items / (spider.processed_items / elapsed_time)  # 剩余分钟数

                # 报告进度
                report_progress({
                    "total_items": spider.total_items,
                    "processed_items": spider.processed_items,
                    "percentage": round(percentage, 2),
                    "processing_speed": round(processing_speed, 2),
                    "estimated_remaining": round(estimated_remaining / 60, 2),  # 转换为小时
                })

        return item

    def close_spider(self, spider):
        """爬虫关闭时的处理"""
        if not hasattr(spider, "task_id") or spider.task_id is None:
            return

        # 生成结果摘要
        stats = spider.crawler_stats
        result_summary = (
            f"总处理项目: {spider.processed_items}, "
            f"成功: {stats.get('success', 0)}, "
            f"失败: {stats.get('failed', 0)}, "
            f"丢弃: {stats.get('dropped', 0)}"
        )
        report_result(result_summary)

        # 报告最终状态
        if hasattr(spider, "error_message"):
            report_status("failed", spider.error_message)
        else:
            report_status("completed")
