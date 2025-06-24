#!/usr/bin/env python3
"""
资源API路由
提供资源相关的查询接口
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ikuyo.api.models.schemas import (
    DataResponse,
    PaginatedResponse,
    PaginationResponse,
    ResourceResponse,
)
from ikuyo.core.database import ResourceRepository

router = APIRouter(prefix="/resources", tags=["Resources"])


def get_resource_repository():
    """获取资源数据仓库"""
    return ResourceRepository()


@router.get("/", response_model=PaginatedResponse)
async def get_resources(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    anime_id: Optional[int] = Query(None, description="动画ID"),
    resolution: Optional[str] = Query(None, description="分辨率"),
    episode: Optional[int] = Query(None, description="集数"),
    repo: ResourceRepository = Depends(get_resource_repository),
):
    """
    获取资源列表
    支持分页和多种过滤条件
    """
    try:
        # 获取过滤后的资源
        resources_data = repo.get_resources_by_filters(
            mikan_id=anime_id,
            resolution=resolution,
            episode_number=episode,
            limit=None,  # 先获取所有数据用于分页计算
        )

        # 分页处理
        offset = (page - 1) * per_page
        total = len(resources_data)
        pages = math.ceil(total / per_page) if total > 0 else 1
        resources_paginated = resources_data[offset : offset + per_page]

        # 转换为响应模型
        resources = [ResourceResponse(**resource) for resource in resources_paginated]

        return PaginatedResponse(
            success=True,
            message="获取资源列表成功",
            pagination=PaginationResponse(page=page, per_page=per_page, total=total, pages=pages),
            data=resources,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源列表失败: {str(e)}")


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource_detail(
    resource_id: int, repo: ResourceRepository = Depends(get_resource_repository)
):
    """
    获取资源详情
    根据资源ID获取详细信息
    """
    try:
        # 通过过滤获取特定资源（使用资源ID查询有些复杂，这里简化处理）
        resources_data = repo.get_resources_by_filters(limit=None)

        # 查找特定ID的资源
        resource_data = None
        for resource in resources_data:
            if resource.get("id") == resource_id:
                resource_data = resource
                break

        if not resource_data:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {resource_id} 的资源")

        return ResourceResponse(**resource_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源详情失败: {str(e)}")


@router.get("/anime/{anime_id}")
async def get_resources_by_anime(
    anime_id: int,
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    resolution: Optional[str] = Query(None, description="分辨率过滤"),
    episode: Optional[int] = Query(None, description="集数过滤"),
    repo: ResourceRepository = Depends(get_resource_repository),
):
    """
    获取指定动画的所有资源
    支持分页和分辨率、集数过滤
    """
    try:
        # 获取特定动画的资源
        resources_data = repo.get_resources_by_filters(
            mikan_id=anime_id, resolution=resolution, episode_number=episode, limit=None
        )

        if not resources_data:
            raise HTTPException(status_code=404, detail=f"未找到动画ID为 {anime_id} 的资源")

        # 分页处理
        offset = (page - 1) * per_page
        total = len(resources_data)
        pages = math.ceil(total / per_page) if total > 0 else 1
        resources_paginated = resources_data[offset : offset + per_page]

        # 转换为响应模型
        resources = [ResourceResponse(**resource) for resource in resources_paginated]

        return PaginatedResponse(
            success=True,
            message=f"获取动画 {anime_id} 的资源成功",
            pagination=PaginationResponse(page=page, per_page=per_page, total=total, pages=pages),
            data=resources,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取动画资源失败: {str(e)}")


@router.get("/search/resolution/{resolution}")
async def search_by_resolution(
    resolution: str,
    limit: int = Query(20, ge=1, le=100, description="结果数量限制"),
    repo: ResourceRepository = Depends(get_resource_repository),
):
    """
    按分辨率搜索资源
    """
    try:
        resources_data = repo.get_resources_by_filters(resolution=resolution, limit=limit)

        # 转换为响应模型
        resources = [ResourceResponse(**resource) for resource in resources_data]

        return DataResponse(
            success=True,
            message=f"找到 {len(resources)} 个 {resolution} 分辨率的资源",
            data=resources,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"按分辨率搜索资源失败: {str(e)}")


@router.get("/latest/{count}")
async def get_latest_resources(
    count: int,
    repo: ResourceRepository = Depends(get_resource_repository),
):
    """
    获取最新发布的资源
    按发布时间倒序排列
    """
    try:
        # 获取所有资源并按发布时间排序
        resources_data = repo.get_resources_by_filters(limit=count)

        # 转换为响应模型
        resources = [ResourceResponse(**resource) for resource in resources_data]

        return DataResponse(
            success=True, message=f"获取最新 {len(resources)} 个资源成功", data=resources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新资源失败: {str(e)}")
