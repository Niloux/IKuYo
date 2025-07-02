#!/usr/bin/env python3
"""
工作器启动脚本
启动多进程并发的爬虫任务处理器
"""

import sys
import os
import argparse

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ikuyo.core.worker.main import WorkerManager
from ikuyo.core.worker.progress_consumer import start_progress_consumer


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="IKuYo 工作器启动脚本")
    parser.add_argument("--workers", type=int, default=3, help="工作进程数量 (默认: 3)")
    parser.add_argument("--verbose", action="store_true", help="详细日志输出")

    args = parser.parse_args()

    print("🚀 IKuYo 多进程工作器")
    print("=" * 40)
    print(f"   工作进程数: {args.workers}")
    print(f"   详细日志: {'开启' if args.verbose else '关闭'}")
    print()

    # 启动进度消费者
    start_progress_consumer()

    # 创建并启动工作器
    worker_manager = WorkerManager(max_workers=args.workers)

    try:
        worker_manager.run()
    except KeyboardInterrupt:
        print("\n👋 工作器已停止")
    except Exception as e:
        print(f"\n❌ 工作器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
