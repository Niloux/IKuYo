#!/usr/bin/env python3
"""
健康检查路由
提供API、数据库和缓存状态检查
"""

from datetime import datetime

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
