from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet.defer import ensureDeferred
from ikuyo.crawler.spiders.mikan import MikanSpider


def run_crawler(args, config):
    """运行爬虫（同步入口）"""
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


class AsyncSpiderRunner:
    def __init__(self):
        self.runner = CrawlerRunner(get_project_settings())

    async def run(
        self,
        config,
        mode,
        year=None,
        season=None,
        start_url=None,
        limit=None,
        progress_callback=None,
    ):
        """
        异步调度 MikanSpider 爬虫。
        参数：config, mode, year, season, start_url, limit, progress_callback
        """
        kwargs = {"mode": mode}
        if year is not None:
            kwargs["year"] = year
        if season is not None:
            kwargs["season"] = season
        if start_url is not None:
            kwargs["start_url"] = start_url
        if limit is not None:
            kwargs["limit"] = limit
        # progress_callback 可扩展
        d = self.runner.crawl(MikanSpider, config, **kwargs)
        try:
            return await ensureDeferred(d)
        except Exception as e:
            # 可扩展异常处理和日志
            raise e
