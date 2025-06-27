#!/usr/bin/env python3
"""
健康检查路由
提供API、数据库和缓存状态检查
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends

from ikuyo.api.models.schemas import HealthResponse
from ikuyo.core.bangumi_service import BangumiService
from ikuyo.core.database import DatabaseManager

router = APIRouter(prefix="/health", tags=["Health"])

# 创建BangumiService实例
bangumi_service = BangumiService()


def get_database():
    """获取数据库连接"""
    db_manager = DatabaseManager()
    try:
        yield db_manager
    finally:
        pass


@router.get("/", response_model=HealthResponse)
async def health_check(db: DatabaseManager = Depends(get_database)):
    """
    健康检查接口
    检查API、数据库和缓存状态
    """
    try:
        # 测试数据库连接（使用读连接池）
        db.execute_one("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # 获取缓存状态
    cache_stats = bangumi_service.get_cache_info()  # 使用BangumiService的get_cache_info方法

    # 获取数据库统计信息
    db_stats = db.get_database_stats()

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.now().isoformat(),
        database_status=db_status,
        cache_stats={**cache_stats, "database": db_stats},
    )


@router.post("/cache/clear")
async def clear_cache(cache_key: Optional[str] = None):
    """
    清理缓存接口
    可选择清理特定缓存或全部缓存
    """
    bangumi_service.clear_cache(cache_key)  # 使用BangumiService的clear_cache方法

    return {
        "message": f"缓存已清理: {cache_key}" if cache_key else "全部缓存已清理",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """
    获取缓存统计信息
    """
    stats = bangumi_service.get_cache_info()  # 使用BangumiService的get_cache_info方法
    return {"cache_stats": stats, "timestamp": datetime.now().isoformat()}


@router.get("/database")
async def get_database_health(db: DatabaseManager = Depends(get_database)):
    """
    获取数据库连接池详细状态
    """
    db_stats = db.get_database_stats()

    return {
        "database_health": {
            "read_pool": {
                "pool_size": db_stats["read_pool"]["pool_size"],
                "available_connections": db_stats["read_pool"]["available_connections"],
                "active_connections": db_stats["read_pool"]["active_connections"],
                "utilization": f"{((db_stats['read_pool']['pool_size'] - db_stats['read_pool']['available_connections']) / db_stats['read_pool']['pool_size'] * 100):.1f}%",
            },
            "write_connection": {
                "status": "healthy" if db_stats["write_connection"]["healthy"] else "unhealthy",
                "wal_mode": db_stats["write_connection"]["wal_mode"],
                "synchronous": db_stats["write_connection"]["synchronous"],
                "cache_size": db_stats["write_connection"]["cache_size"],
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/database/reset")
async def reset_database_connections(db: DatabaseManager = Depends(get_database)):
    """
    重置数据库连接池
    紧急情况下使用
    """
    try:
        # 关闭所有连接
        db.close_all()

        # 重新初始化连接池和写连接
        db.read_pool = db.read_pool.__class__(str(db.db_path), db.read_pool_size, db.read_timeout)

        db.write_manager = db.write_manager.__class__(str(db.db_path), db.write_timeout)

        return {
            "success": True,
            "message": "数据库连接池已重置",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"重置失败: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }
