"""
数据去重和增量管理Pipeline
实现智能去重机制、增量更新和数据合并功能
"""

import datetime
import hashlib
import json
from typing import Any, Dict, Optional

from scrapy import signals
from scrapy.exceptions import DropItem

from src.config import get_config


class DeduplicationPipeline:
    """数据去重Pipeline"""

    def __init__(self):
        self.seen_items = set()
        self.duplicate_count = 0
        self.total_count = 0

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        """爬虫开始时初始化"""
        spider.logger.info("初始化数据去重Pipeline")

    def spider_closed(self, spider):
        """爬虫结束时统计"""
        spider.logger.info(
            f"去重统计: 总处理 {self.total_count} 项, "
            f"去重 {self.duplicate_count} 项, "
            f"保留 {self.total_count - self.duplicate_count} 项"
        )

    def process_item(self, item, spider):
        """处理数据项，进行去重"""
        self.total_count += 1

        # 生成唯一标识
        item_hash = self._generate_item_hash(item)

        # 检查是否重复
        if item_hash in self.seen_items:
            self.duplicate_count += 1
            spider.logger.debug(f"发现重复项: {item.get('title', 'Unknown')}")
            raise DropItem(f"重复项: {item.get('title', 'Unknown')}")

        # 添加到已见集合
        self.seen_items.add(item_hash)

        # 添加去重信息
        item["deduplication_hash"] = item_hash
        item["processed_at"] = datetime.datetime.now().isoformat()

        return item

    def _generate_item_hash(self, item: Dict[str, Any]) -> str:
        """生成数据项的唯一哈希值"""
        # 根据数据类型生成不同的哈希
        if "mikan_id" in item:
            # 动画数据：基于mikan_id和标题
            key_data = f"{item.get('mikan_id')}_{item.get('title', '')}"
        elif "group_id" in item:
            # 字幕组数据：基于group_id和group_name
            key_data = f"{item.get('group_id')}_{item.get('group_name', '')}"
        elif "magnet_link" in item:
            # 资源数据：基于mikan_id、group_id和magnet_link
            key_data = (
                f"{item.get('mikan_id')}_{item.get('group_id')}_{item.get('magnet_link', '')}"
            )
        else:
            # 其他数据：基于所有字段
            key_data = json.dumps(item, sort_keys=True, ensure_ascii=False)

        return hashlib.md5(key_data.encode("utf-8")).hexdigest()


class IncrementalUpdatePipeline:
    """增量更新Pipeline"""

    def __init__(self):
        self.last_crawl_time = None
        self.updated_items = 0
        self.new_items = 0

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        """爬虫开始时初始化"""
        spider.logger.info("初始化增量更新Pipeline")

        # 获取上次爬取时间
        incremental_config = get_config("crawl_mode", "incremental")
        self.last_crawl_time = incremental_config.get("last_crawl_time")

        if self.last_crawl_time:
            spider.logger.info(f"上次爬取时间: {self.last_crawl_time}")
        else:
            spider.logger.info("首次爬取，将处理所有数据")

    def spider_closed(self, spider):
        """爬虫结束时统计"""
        spider.logger.info(f"增量更新统计: 新增 {self.new_items} 项, 更新 {self.updated_items} 项")

        # 更新最后爬取时间
        current_time = datetime.datetime.now().isoformat()
        # 这里可以保存到配置文件或数据库
        spider.logger.info(f"更新最后爬取时间: {current_time}")

    def process_item(self, item, spider):
        """处理数据项，进行增量更新"""
        # 检查是否为增量模式
        if not hasattr(spider, "mode") or spider.mode != "incremental":
            return item

        # 检查数据时间
        if self._is_new_item(item):
            self.new_items += 1
            item["update_type"] = "new"
            spider.logger.debug(f"新增项: {item.get('title', 'Unknown')}")
        else:
            self.updated_items += 1
            item["update_type"] = "updated"
            spider.logger.debug(f"更新项: {item.get('title', 'Unknown')}")

        # 添加增量更新信息
        item["incremental_processed"] = True
        item["last_crawl_time"] = self.last_crawl_time
        item["current_crawl_time"] = datetime.datetime.now().isoformat()

        return item

    def _is_new_item(self, item: Dict[str, Any]) -> bool:
        """判断是否为新增项"""
        if not self.last_crawl_time:
            return True

        # 检查数据中的时间字段
        item_time = self._extract_item_time(item)
        if not item_time:
            return True

        # 比较时间
        try:
            item_datetime = datetime.datetime.fromisoformat(item_time.replace("Z", "+00:00"))
            last_datetime = datetime.datetime.fromisoformat(
                self.last_crawl_time.replace("Z", "+00:00")
            )
            return item_datetime > last_datetime
        except:
            return True

    def _extract_item_time(self, item: Dict[str, Any]) -> Optional[str]:
        """提取数据项中的时间字段"""
        # 尝试多个可能的时间字段
        time_fields = ["created_at", "updated_at", "release_date", "date"]

        for field in time_fields:
            if field in item and item[field]:
                return item[field]

        return None


class DataMergePipeline:
    """数据合并Pipeline"""

    def __init__(self):
        self.merged_items = 0

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        """爬虫开始时初始化"""
        spider.logger.info("初始化数据合并Pipeline")

    def spider_closed(self, spider):
        """爬虫结束时统计"""
        spider.logger.info(f"数据合并统计: 合并 {self.merged_items} 项")

    def process_item(self, item, spider):
        """处理数据项，进行数据合并"""
        # 检查是否需要合并
        if self._needs_merge(item):
            item = self._merge_item(item, spider)
            self.merged_items += 1

        return item

    def _needs_merge(self, item: Dict[str, Any]) -> bool:
        """检查是否需要合并"""
        # 检查是否有重复的mikan_id
        if "mikan_id" in item:
            # 这里可以实现更复杂的合并逻辑
            return False

        return False

    def _merge_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """合并数据项"""
        # 这里可以实现具体的数据合并逻辑
        # 例如：合并相同动画的不同资源信息
        spider.logger.debug(f"合并数据项: {item.get('title', 'Unknown')}")

        # 添加合并标记
        item["merged"] = True
        item["merge_time"] = datetime.datetime.now().isoformat()

        return item


class CrawlHistoryPipeline:
    """爬取历史记录Pipeline"""

    def __init__(self):
        self.crawl_history = []

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        """爬虫开始时初始化"""
        spider.logger.info("初始化爬取历史Pipeline")

        # 记录爬取开始信息
        self.crawl_start = {
            "spider_name": spider.name,
            "start_time": datetime.datetime.now().isoformat(),
            "crawl_mode": getattr(spider, "mode", "unknown"),
            "crawl_year": getattr(spider, "year", None),
            "crawl_season": getattr(spider, "season", None),
        }

    def spider_closed(self, spider):
        """爬虫结束时记录历史"""
        # 记录爬取结束信息
        crawl_end = {
            "end_time": datetime.datetime.now().isoformat(),
            "status": "completed",
            "total_items": len(self.crawl_history),
        }

        # 合并爬取信息
        crawl_record = {**self.crawl_start, **crawl_end}

        # 保存爬取历史
        self._save_crawl_history(crawl_record, spider)

        spider.logger.info(f"爬取历史已记录: {crawl_record}")

    def process_item(self, item, spider):
        """处理数据项，记录历史"""
        # 记录数据项信息
        item_record = {
            "item_type": item.__class__.__name__,
            "item_id": item.get("mikan_id") or item.get("group_id") or "unknown",
            "title": item.get("title") or item.get("group_name") or "unknown",
            "processed_time": datetime.datetime.now().isoformat(),
        }

        self.crawl_history.append(item_record)

        return item

    def _save_crawl_history(self, crawl_record: Dict[str, Any], spider):
        """保存爬取历史"""
        # 这里可以实现保存到数据库或文件的逻辑
        # 暂时只记录日志
        spider.logger.info(
            f"爬取历史记录: {json.dumps(crawl_record, ensure_ascii=False, indent=2)}"
        )


# 组合Pipeline
class ComprehensiveDataPipeline:
    """综合数据处理Pipeline"""

    def __init__(self):
        self.deduplication = DeduplicationPipeline()
        self.incremental = IncrementalUpdatePipeline()
        self.merge = DataMergePipeline()
        self.history = CrawlHistoryPipeline()

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        """爬虫开始时初始化所有Pipeline"""
        self.deduplication.spider_opened(spider)
        self.incremental.spider_opened(spider)
        self.merge.spider_opened(spider)
        self.history.spider_opened(spider)

    def spider_closed(self, spider):
        """爬虫结束时关闭所有Pipeline"""
        self.deduplication.spider_closed(spider)
        self.incremental.spider_closed(spider)
        self.merge.spider_closed(spider)
        self.history.spider_closed(spider)

    def process_item(self, item, spider):
        """按顺序处理数据项"""
        # 1. 去重
        try:
            item = self.deduplication.process_item(item, spider)
        except DropItem:
            return item

        # 2. 增量更新
        item = self.incremental.process_item(item, spider)

        # 3. 数据合并
        item = self.merge.process_item(item, spider)

        # 4. 记录历史
        item = self.history.process_item(item, spider)

        return item
