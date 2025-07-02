from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ikuyo.crawler.spiders.mikan import MikanSpider
import os


def run_crawler(args, config):
    """运行爬虫（同步入口）"""
    with open("./worker_debug.log", "a") as f:
        f.write(
            f"[DEBUG] run_crawler called: PID={os.getpid()}, args={getattr(args, '__dict__', str(args))}, config={config}\n"
        )
    try:
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
        with open("./worker_debug.log", "a") as f:
            f.write("[DEBUG] Before process.crawl and process.start()\n")
        process.crawl(MikanSpider, **spider_kwargs)
        process.start()
        with open("./worker_debug.log", "a") as f:
            f.write("[DEBUG] After process.start()\n")
    except Exception as e:
        with open("./worker_debug.log", "a") as f:
            f.write(f"[ERROR] run_crawler exception: {e}\n")
        import traceback

        traceback.print_exc()
