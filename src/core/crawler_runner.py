from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from src.crawler.spiders.mikan import MikanSpider


def run_crawler(args, config):
    """运行爬虫（唯一入口）"""
    settings = get_project_settings()
    settings.set("LOG_LEVEL", getattr(args, "log_level", "INFO"))
    if getattr(args, "output", None):
        settings.set("FEED_FORMAT", "json")
        settings.set("FEED_URI", args.output)
    process = CrawlerProcess(settings)
    spider_kwargs = {"config": config, "mode": getattr(args, "mode", "homepage")}
    if getattr(args, "year", None):
        spider_kwargs["year"] = args.year
    if getattr(args, "season", None):
        spider_kwargs["season"] = args.season
    if getattr(args, "start_url", None):
        spider_kwargs["start_url"] = args.start_url
    if getattr(args, "limit", None) is not None:
        spider_kwargs["limit"] = args.limit
    process.crawl(MikanSpider, **spider_kwargs)
    process.start()
