#!/usr/bin/env python3
"""
定时任务管理脚本
支持启动、停止、查看任务状态等操作
"""

import argparse
import logging
import os

# 指定项目根目录
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import load_config
from src.core.scheduler import CrawlerScheduler


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


def show_status():
    """显示任务状态"""

    # 检查是否启用定时任务
    config = load_config()
    scheduler_config = getattr(config, "scheduler", {})

    if not getattr(scheduler_config, "enabled", False):
        print("❌ 定时任务未启用")
        return

    print("📋 定时任务状态:")
    print(f"   启用状态: {'✅ 已启用' if getattr(scheduler_config, 'enabled') else '❌ 未启用'}")
    print(f"   时区设置: {getattr(scheduler_config, 'timezone', 'Asia/Shanghai')}")

    # 显示任务配置
    jobs = getattr(scheduler_config, "jobs", [])
    print("\n📅 任务配置:")
    for job in jobs:
        status = "✅ 启用" if getattr(job, "enabled", True) else "❌ 禁用"
        print(f"   {getattr(job, 'name')} ({getattr(job, 'id')})")
        print(f"     状态: {status}")
        print(f"     调度: {getattr(job, 'cron')}")
        print(f"     描述: {getattr(job, 'description', '无')}")
        print()


def start_scheduler():
    """启动调度器"""
    print("🚀 启动定时任务调度器...")

    scheduler = CrawlerScheduler()
    if scheduler.start():
        print("✅ 调度器启动成功")
        print("💡 提示: 使用 Ctrl+C 停止调度器")

        try:
            # 保持运行
            import time

            while scheduler.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  收到停止信号...")
            scheduler.stop()
            print("✅ 调度器已停止")
    else:
        print("❌ 调度器启动失败")


def test_job():
    """测试执行一次爬虫任务"""
    print("🧪 测试执行爬虫任务...")

    scheduler = CrawlerScheduler()
    if scheduler.init_scheduler():
        try:
            scheduler._run_crawler()
            print("✅ 测试任务执行成功")
        except Exception as e:
            print(f"❌ 测试任务执行失败: {e}")
    else:
        print("❌ 调度器初始化失败")


def show_help():
    """显示帮助信息"""
    help_text = """
IKuYo 定时任务管理工具

使用方法:
  python manage_scheduler.py <命令> [选项]

可用命令:
  status    显示任务状态和配置
  start     启动定时任务调度器
  test      测试执行一次爬虫任务
  help      显示此帮助信息

示例:
  python manage_scheduler.py status    # 查看任务状态
  python manage_scheduler.py start     # 启动调度器
  python manage_scheduler.py test      # 测试爬虫任务

配置说明:
  定时任务配置在 config.py 的 SCHEDULER_CONFIG 中
  支持 cron 表达式格式: "分 时 日 月 周"
  默认每天凌晨2点执行: "0 2 * * *"
"""
    print(help_text)


def main():
    """主函数"""
    config = load_config()
    scheduler_config = getattr(config, "scheduler", {})

    if not getattr(scheduler_config, "enabled", False):
        print("❌ 定时任务未启用")
        return

    print("📅 IKuYo 定时任务管理器")
    print("=" * 40)
    print(f"   启用状态: {'✅ 已启用' if getattr(scheduler_config, 'enabled') else '❌ 未启用'}")
    print(f"   时区设置: {getattr(scheduler_config, 'timezone', 'Asia/Shanghai')}")
    print()

    jobs = getattr(scheduler_config, "jobs", [])

    setup_logging()

    parser = argparse.ArgumentParser(description="IKuYo 定时任务管理工具", add_help=False)
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["status", "start", "test", "help"],
        help="要执行的命令",
    )

    args = parser.parse_args()

    # 执行对应命令
    if args.command == "status":
        show_status()
    elif args.command == "start":
        start_scheduler()
    elif args.command == "test":
        test_job()
    else:
        show_help()


if __name__ == "__main__":
    main()
