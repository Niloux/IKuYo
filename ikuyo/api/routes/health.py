#!/usr/bin/env python3
"""
健康检查路由
提供API和数据库状态检查
"""

from datetime import datetime

from fastapi import APIRouter, Depends

from ikuyo.api.models.schemas import HealthResponse
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
    检查API和数据库状态
    """
    try:
        # 测试数据库连接
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.now().isoformat(),
        database_status=db_status,
    )
