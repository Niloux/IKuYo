# Scrapy settings for ikuyo project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html


from src.ikuyo.config import get_config

BOT_NAME = "ikuyo"

SPIDER_MODULES = ["src.ikuyo.crawler.spiders"]
NEWSPIDER_MODULE = "src.ikuyo.crawler.spiders"

# 从配置文件获取设置
CRAWLER_CONFIG = get_config("crawler")

# 爬虫设置
DOWNLOAD_DELAY = CRAWLER_CONFIG["download_delay"]
CONCURRENT_REQUESTS = CRAWLER_CONFIG["concurrent_requests"]

# 重试设置
RETRY_TIMES = CRAWLER_CONFIG["retry_times"]

# 遵守robots.txt规则
ROBOTSTXT_OBEY = True

# 禁用cookies (默认启用)
COOKIES_ENABLED = False

# 禁用Telnet控制台 (默认启用)
# TELNETCONSOLE_ENABLED = False

# 覆盖默认请求头:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# 启用或禁用spider中间件
# 查看 https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "ikuyo_scrapy.middlewares.IkuyoScrapySpiderMiddleware": 543,
# }

# 启用或禁用下载器中间件
# 查看 https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    "ikuyo_scrapy.middlewares.IkuyoScrapyDownloaderMiddleware": 543,
# }

# 启用或禁用扩展
# 查看 https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "src.ikuyo.crawler.pipelines.ValidationPipeline": 100,
    "src.ikuyo.crawler.pipelines.DuplicatesPipeline": 200,
    "src.ikuyo.crawler.pipelines.SQLitePipeline": 300,
    # "src.ikuyo.crawler.pipelines.JsonWriterPipeline": 400,
}

# 启用和配置HTTP缓存 (默认禁用)
# 查看 https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# 设置文件下载的默认用户代理
# USER_AGENT = "ikuyo_scrapy (+http://www.yourdomain.com)"

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Set settings whose default value is deprecated to a future-proof value.
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"

# 输出设置
# FEEDS = {
#     "output/anime_%(time)s.json": {
#         "format": "json",
#         "encoding": "utf8",
#         "indent": 2,
#         "overwrite": True,
#     },
# }
