#!/usr/bin/env python3
"""
IKuYo 爬虫运行脚本
"""

import argparse

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="IKuYo 爬虫运行脚本")
    parser.add_argument("--limit", type=int, help="限制爬取的动画数量（测试模式）")
    parser.add_argument("--url", type=str, help="指定起始URL")
    parser.add_argument("--test", action="store_true", help="启用测试模式")

    args = parser.parse_args()

    # 获取项目设置
    settings = get_project_settings()

    # 如果指定了测试模式，更新配置
    if args.test:
        settings.set(
            "CRAWLER_CONFIG",
            {**settings.get("CRAWLER_CONFIG"), "test_mode": True, "test_limit": args.limit or 3},
        )

    # 创建爬虫进程
    process = CrawlerProcess(settings)

    # 准备爬虫参数
    spider_kwargs = {}
    if args.limit:
        spider_kwargs["limit"] = args.limit
    if args.url:
        spider_kwargs["start_url"] = args.url

    # 启动爬虫
    process.crawl("mikan", **spider_kwargs)
    process.start()


if __name__ == "__main__":
    main()
