#!/usr/bin/env python3
"""
健康检查路由
提供API、数据库和缓存状态检查
"""

from datetime import datetime

from fastapi import APIRouter
from sqlmodel import select

from ikuyo.api.models.schemas import HealthResponse
from ikuyo.core.bangumi_service import BangumiService
from ikuyo.core.database import get_session
from ikuyo.core.repositories import AnimeRepository

router = APIRouter(prefix="/health", tags=["Health"])

# 创建BangumiService实例
bangumi_service = BangumiService()


@router.get("", response_model=HealthResponse)
def health_check():
    """
    健康检查接口
    检查API、数据库和缓存状态
    """
    try:
        # 测试数据库连接（ORM方式）
        with get_session() as session:
            # 尝试ORM查询
            session.exec(select(1)).first()
            db_status = "healthy"
            # 数据库统计信息（以Anime表为例，可扩展）
            anime_repo = AnimeRepository(session)
            anime_count = len(anime_repo.list(limit=1_000_000))
            db_stats = {"anime_count": anime_count}
    except Exception:
        db_status = "unhealthy"
        db_stats = {}

    # 获取缓存状态
    def to_dict_if_config(val):
        if hasattr(val, "__dict__"):
            return {k: to_dict_if_config(v) for k, v in val.__dict__.items()}
        elif isinstance(val, dict):
            return {k: to_dict_if_config(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [to_dict_if_config(v) for v in val]
        else:
            return val

    cache_stats = dict(to_dict_if_config(bangumi_service.get_cache_info()))

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "unhealthy",
        version="2.0.0",
        timestamp=datetime.now().isoformat(),
        database_status=db_status,
        cache_stats={**cache_stats, "database": db_stats},
    )
