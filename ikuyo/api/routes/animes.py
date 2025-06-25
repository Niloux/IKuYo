#!/usr/bin/env python3
"""
动画API路由
提供动画相关的查询接口
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ikuyo.api.models.schemas import (
    AnimeDetailResponse,
    AnimeResponse,
    DataResponse,
    PaginatedResponse,
    PaginationResponse,
)
from ikuyo.core.database import AnimeRepository

router = APIRouter(prefix="/animes", tags=["Animes"])


def get_anime_repository():
    """获取动画数据仓库"""
    return AnimeRepository()


@router.get("/", response_model=PaginatedResponse)
async def get_animes(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    q: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="动画状态"),
    repo: AnimeRepository = Depends(get_anime_repository),
):
    """
    获取动画列表
    支持分页和搜索
    """
    try:
        offset = (page - 1) * per_page

        if q:
            # 搜索模式
            animes_data = repo.search_animes_by_title(q)
        else:
            # 列表模式
            animes_data = repo.get_all_animes()

        # 状态过滤
        if status:
            animes_data = [anime for anime in animes_data if anime.get("status") == status]

        # 计算分页
        total = len(animes_data)
        pages = math.ceil(total / per_page) if total > 0 else 1

        # 应用分页
        animes_paginated = animes_data[offset : offset + per_page]

        # 转换为响应模型
        animes = [AnimeResponse(**anime) for anime in animes_paginated]

        return PaginatedResponse(
            success=True,
            message="获取动画列表成功",
            pagination=PaginationResponse(page=page, per_page=per_page, total=total, pages=pages),
            data=animes,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取动画列表失败: {str(e)}")


@router.get("/{mikan_id}", response_model=AnimeDetailResponse)
async def get_anime_detail(mikan_id: int, repo: AnimeRepository = Depends(get_anime_repository)):
    """
    获取动画详情
    包含动画基本信息和相关资源
    """
    try:
        # 获取动画基本信息
        anime_data = repo.get_anime_by_id(mikan_id)
        if not anime_data:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {mikan_id} 的动画")

        # 获取相关资源
        resources_data = repo.get_anime_resources(mikan_id)

        # 获取字幕组信息（从资源中提取）
        subtitle_groups = {}
        for resource in resources_data:
            sg_id = resource.get("subtitle_group_id")
            sg_name = resource.get("subtitle_group_name")
            if sg_id and sg_name and sg_id not in subtitle_groups:
                subtitle_groups[sg_id] = {
                    "id": sg_id,
                    "name": sg_name,
                }

        # 构建详情响应
        from ikuyo.api.models.schemas import ResourceResponse

        resources = [ResourceResponse(**resource) for resource in resources_data]

        anime_detail = AnimeDetailResponse(
            **anime_data, resources=resources, subtitle_groups=list(subtitle_groups.values())
        )

        return anime_detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取动画详情失败: {str(e)}")


@router.get("/{mikan_id}/resources")
async def get_anime_resources(
    mikan_id: int,
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    repo: AnimeRepository = Depends(get_anime_repository),
):
    """
    获取指定动画的资源列表
    支持分页
    """
    try:
        # 验证动画是否存在
        anime = repo.get_anime_by_id(mikan_id)
        if not anime:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {mikan_id} 的动画")

        # 获取资源
        resources_data = repo.get_anime_resources(mikan_id)

        # 分页处理
        offset = (page - 1) * per_page
        total = len(resources_data)
        pages = math.ceil(total / per_page) if total > 0 else 1
        resources_paginated = resources_data[offset : offset + per_page]

        return PaginatedResponse(
            success=True,
            message="获取动画资源成功",
            pagination=PaginationResponse(page=page, per_page=per_page, total=total, pages=pages),
            data=resources_paginated,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取动画资源失败: {str(e)}")


@router.get("/search/{keyword}")
async def search_animes(
    keyword: str,
    limit: int = Query(10, ge=1, le=50, description="结果数量限制"),
    repo: AnimeRepository = Depends(get_anime_repository),
):
    """
    搜索动画
    根据关键词搜索动画标题
    """
    try:
        animes_data = repo.search_animes_by_title(keyword)

        # 限制结果数量
        animes_limited = animes_data[:limit]

        # 转换为响应模型
        animes = [AnimeResponse(**anime) for anime in animes_limited]

        return DataResponse(success=True, message=f"找到 {len(animes)} 个匹配的动画", data=animes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索动画失败: {str(e)}")
