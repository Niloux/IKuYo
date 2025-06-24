#!/usr/bin/env python3
"""
健康检查路由
提供API和数据库状态检查
"""

import time

from fastapi import APIRouter, Depends, HTTPException

from ikuyo.api.models.schemas import HealthResponse, StatsResponse
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
        status="healthy", version="1.0.0", timestamp=int(time.time()), database_status=db_status
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: DatabaseManager = Depends(get_database)):
    """
    获取统计信息
    返回数据库中的统计数据
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # 获取动画总数
            cursor.execute("SELECT COUNT(*) FROM animes")
            total_animes = cursor.fetchone()[0]

            # 获取资源总数
            cursor.execute("SELECT COUNT(*) FROM resources")
            total_resources = cursor.fetchone()[0]

            # 获取字幕组总数
            cursor.execute("SELECT COUNT(*) FROM subtitle_groups")
            total_subtitle_groups = cursor.fetchone()[0]

            # 获取最新更新时间
            cursor.execute(
                "SELECT MAX(updated_at) FROM animes UNION SELECT MAX(updated_at) FROM resources ORDER BY 1 DESC LIMIT 1"  # noqa: E501
            )
            result = cursor.fetchone()
            latest_update = result[0] if result else None

        return StatsResponse(
            total_animes=total_animes,
            total_resources=total_resources,
            total_subtitle_groups=total_subtitle_groups,
            latest_update=latest_update,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
