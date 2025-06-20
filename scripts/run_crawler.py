#!/usr/bin/env python3
"""
Mikan Project 爬虫运行脚本
支持多种爬取模式：首页模式、年份模式、季度模式、全量模式、增量模式
"""

import argparse
import datetime
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


from src.config import load_config
from src.core.crawler_runner import run_crawler


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Mikan Project 爬虫 - 支持多种爬取模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 首页模式（默认）
  python scripts/run_crawler.py
  
  # 年份模式 - 爬取2024年所有季度
  python scripts/run_crawler.py --mode year --year 2024
  
  # 季度模式 - 爬取2024年春季
  python scripts/run_crawler.py --mode season --year 2024 --season 春
  
  # 全量模式 - 爬取2013年至今所有动画
  python scripts/run_crawler.py --mode full
  
  # 增量模式 - 只爬取新增动画
  python scripts/run_crawler.py --mode incremental
  
  # 限制爬取数量
  python scripts/run_crawler.py --limit 5
        """,
    )

    # 爬取模式参数
    parser.add_argument(
        "--mode",
        choices=["homepage", "year", "season", "full", "incremental"],
        default="homepage",
        help="爬取模式 (默认: homepage)",
    )

    # 年份参数
    parser.add_argument("--year", type=int, help="爬取年份 (年份模式和季度模式时使用)")

    # 季度参数
    parser.add_argument(
        "--season", choices=["春", "夏", "秋", "冬"], help="爬取季度 (季度模式时使用)"
    )

    # 限制参数
    parser.add_argument("--limit", type=int, help="爬取数量限制")

    # 起始URL参数
    parser.add_argument("--start-url", help="指定起始URL，直接爬取指定动画")

    # 输出参数
    parser.add_argument("--output", help="输出文件路径 (JSON格式)")

    # 日志参数
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)",
    )

    # 配置参数
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")

    return parser.parse_args()


def validate_arguments(args):
    """验证命令行参数"""
    errors = []
    current_year = datetime.datetime.now().year

    # 检查年份模式参数
    if args.mode == "year":
        if not args.year:
            errors.append("年份模式需要指定 --year 参数")
        elif args.year < 2013 or args.year > current_year + 1:
            errors.append(f"年份必须在 2013-{current_year + 1} 范围内")

    # 检查季度模式参数
    if args.mode == "season":
        if not args.year:
            errors.append("季度模式需要指定 --year 参数")
        elif args.year < 2013 or args.year > current_year + 1:
            errors.append(f"年份必须在 2013-{current_year + 1} 范围内")
        if not args.season:
            errors.append("季度模式需要指定 --season 参数")

    # 检查限制参数
    if args.limit and args.limit <= 0:
        errors.append("数量限制必须大于0")

    if errors:
        print("参数错误:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


def print_crawl_info(args, config):
    """打印爬取信息"""
    print("=" * 60)
    print("Mikan Project 爬虫")
    print("=" * 60)

    print(f"爬取模式: {args.mode}")

    if args.mode == "homepage":
        print("目标: 首页展示的动画")
    elif args.mode == "year":
        print(f"目标: {args.year}年所有季度动画")
    elif args.mode == "season":
        print(f"目标: {args.year}年{args.season}季动画")
    elif args.mode == "full":
        current_year = datetime.datetime.now().year
        print(f"目标: 2013-{current_year}年所有动画")
    elif args.mode == "incremental":
        print("目标: 增量更新动画")

    limit = args.limit if args.limit is not None else getattr(config, "limit", None)
    if limit:
        print(f"数量限制: {limit} 个动画")

    if args.start_url:
        print(f"起始URL: {args.start_url}")

    print(f"日志级别: {args.log_level}")
    print("=" * 60)


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()

    # 验证参数
    if not validate_arguments(args):
        sys.exit(1)

    # 加载配置文件
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        sys.exit(1)

    # 打印爬取信息
    print_crawl_info(args, config)

    # 确认是否继续
    if args.mode in ["full", "year"]:
        print("\n⚠️  警告: 这将爬取大量数据，可能需要很长时间")
        response = input("是否继续? (y/N): ")
        if response.lower() not in ["y", "yes"]:
            print("已取消爬取")
            sys.exit(0)

    # 运行爬虫
    try:
        run_crawler(args, config)
        print("✅ 爬取成功完成")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 爬取失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
