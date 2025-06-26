#!/usr/bin/env python3
"""
健康检查路由
提供API、数据库和缓存状态检查
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends

from ikuyo.api.models.schemas import HealthResponse
from ikuyo.core.bangumi_service import bangumi_service
from ikuyo.core.database import DatabaseManager

router = APIRouter(prefix="/health", tags=["Health"])


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
        # 测试数据库连接
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # 获取缓存状态
    cache_stats = bangumi_service.get_cache_stats()

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.now().isoformat(),
        database_status=db_status,
        cache_stats=cache_stats,
    )


@router.post("/cache/clear")
async def clear_cache(cache_key: Optional[str] = None):
    """
    清理缓存接口
    可选择清理特定缓存或全部缓存
    """
    bangumi_service.clear_cache(cache_key)

    return {
        "message": f"缓存已清理: {cache_key}" if cache_key else "全部缓存已清理",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """
    获取缓存统计信息
    """
    stats = bangumi_service.get_cache_stats()
    return {"cache_stats": stats, "timestamp": datetime.now().isoformat()}
