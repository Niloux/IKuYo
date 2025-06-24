#!/usr/bin/env python3
"""
API服务启动脚本
启动IKuYo动漫资源查询API服务
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn


def main():
    """启动API服务"""
    parser = argparse.ArgumentParser(description="IKuYo动漫资源API服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")

    args = parser.parse_args()

    # 确定日志级别
    log_level = "debug" if args.debug else "info"

    print("🚀 启动IKuYo动漫资源API服务...")
    print(f"📍 地址: http://{args.host}:{args.port}")
    print(f"📚 API文档: http://{args.host}:{args.port}/docs")
    print(f"🔍 健康检查: http://{args.host}:{args.port}/api/v1/health/")
    print(f"🔧 重载模式: {'开启' if args.reload else '关闭'}")
    print(f"🐛 调试模式: {'开启' if args.debug else '关闭'}")
    print("=" * 50)

    # 启动服务
    uvicorn.run(
        "ikuyo.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=["ikuyo"] if args.reload else None,
        log_level=log_level,
        access_log=True,
    )


if __name__ == "__main__":
    main()
