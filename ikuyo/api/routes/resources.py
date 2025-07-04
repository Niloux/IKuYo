#!/usr/bin/env python3
"""
资源API路由
专注于资源获取场景
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from ikuyo.api.models.schemas import (
    EpisodeAvailabilityResponse,
    EpisodeResourcesResponse,
    ErrorResponse,
    SubtitleGroupResource,
)
from ikuyo.core.database import get_session
from ikuyo.core.repositories import (
    AnimeRepository,
    ResourceRepository,
    SubtitleGroupRepository,
)

router = APIRouter(prefix="/animes", tags=["Resources"])


def get_subtitle_type_priority(subtitle_type: str) -> int:
    """获取字幕类型优先级（数字越小优先级越高）"""
    priority_map = {
        # 双语类（最高优先级）
        "中日双语": 1,  # 中文+日语双语（最受欢迎）
        # 单语类
        "简体中文": 2,  # 简体中文字幕
        "繁体中文": 3,  # 繁体中文字幕
        "中文字幕": 4,  # 通用中文字幕
        "英语": 5,  # 英语字幕
        # 其他类
        "简繁双语": 6,  # 简繁体双语
        "简繁日": 7,  # 简繁日双语
        "简繁英": 8,  # 简繁英双语
        "多语字幕": 9,  # 英语等其他语言
        "无字幕": 10,  # 生肉/无字幕
        "其他": 11,  # 未分类
    }
    return priority_map.get(subtitle_type or "", 99)


def get_resolution_priority(resolution: str) -> int:
    """获取分辨率优先级（数字越小优先级越高）"""
    priority_map = {
        "2160p": 1,
        "1080p": 2,
        "720p": 3,
        "480p": 4,
        "420p": 5,
    }
    return priority_map.get(resolution or "", 99)


@router.get(
    "/{bangumi_id}/resources",
    response_model=EpisodeResourcesResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_anime_resources(
    bangumi_id: int = Path(..., description="Bangumi ID"),
    episode: Optional[int] = Query(None, description="指定集数，不提供则返回所有集数"),
    resolution: Optional[str] = Query(None, description="分辨率筛选"),
    subtitle_type: Optional[str] = Query(None, description="字幕类型筛选"),
    limit: int = Query(100, description="返回数量限制", ge=1, le=9999),
    offset: int = Query(0, description="偏移量", ge=0),
):
    """
    统一的资源接口
    支持获取特定集数的资源或全番剧资源，按字幕组分类展示
    """
    try:
        with get_session() as session:
            anime_repo = AnimeRepository(session)
            resource_repo = ResourceRepository(session)
            subtitle_group_repo = SubtitleGroupRepository(session)

            anime = anime_repo.get_by_bangumi_id(bangumi_id)
            if not anime:
                raise HTTPException(
                    status_code=404, detail=f"未找到 bangumi_id={bangumi_id} 的番剧"
                )
            mikan_id = int(anime.mikan_id or 0)

            # 构建ORM过滤条件
            resources = resource_repo.filter(
                mikan_id=mikan_id,
                resolution=resolution,
                episode_number=episode,
                subtitle_type=subtitle_type,
                limit=limit,
            )

            # 获取总数
            total_resources = len(resources)
            if not resources:
                error_msg = (
                    f"未找到番剧 {bangumi_id} 第 {episode} 集的资源"
                    if episode is not None
                    else "该番剧暂无可用资源"
                )
                data = {
                    "bangumi_id": bangumi_id,
                    "episode": episode,
                    "total_resources": 0,
                    "subtitle_groups": [],
                    "filters": {
                        "resolution": resolution,
                        "subtitle_type": subtitle_type,
                    },
                    "pagination": {
                        "limit": limit,
                        "offset": offset,
                        "total": total_resources,
                    },
                }
                return EpisodeResourcesResponse(
                    success=True, message=error_msg, data=data
                )

            # 按字幕组分类
            subtitle_groups: Dict[int, Dict] = {}
            for resource in resources:
                group_id = int(resource.subtitle_group_id or 0)
                group = subtitle_group_repo.get_by_id(group_id)
                group_name = group.name if group else "未知字幕组"
                if group_id not in subtitle_groups:
                    subtitle_groups[group_id] = {
                        "id": group_id,
                        "name": group_name,
                        "resource_count": 0,
                        "resources": [],
                    }
                resource_obj = SubtitleGroupResource(
                    id=int(resource.id or 0),
                    title=resource.title or "",
                    resolution=resource.resolution or "",
                    subtitle_type=resource.subtitle_type or "",
                    file_size=resource.file_size or "",
                    magnet_url=resource.magnet_url or "",
                    torrent_url=resource.torrent_url or "",
                    release_date=(
                        datetime.fromtimestamp(resource.release_date).isoformat()
                        if resource.release_date
                        else None
                    ),
                )
                subtitle_groups[group_id]["resources"].append(resource_obj)
                subtitle_groups[group_id]["resource_count"] += 1

            # 对每个字幕组内的资源进行排序
            for group_data in subtitle_groups.values():
                group_data["resources"].sort(
                    key=lambda x: (
                        int(x.title.split("第")[-1].split("集")[0])
                        if "第" in x.title and "集" in x.title
                        else 999,
                        get_subtitle_type_priority(x.subtitle_type),
                        get_resolution_priority(x.resolution),
                    )
                )

            data = {
                "bangumi_id": bangumi_id,
                "episode": episode,
                "total_resources": total_resources,
                "subtitle_groups": list(subtitle_groups.values()),
                "filters": {"resolution": resolution, "subtitle_type": subtitle_type},
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_resources,
                },
            }
            return EpisodeResourcesResponse(
                success=True, message="获取资源成功", data=data
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源失败: {str(e)}")


@router.get(
    "/{bangumi_id}/episodes/availability",
    response_model=EpisodeAvailabilityResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_episodes_availability(
    bangumi_id: int = Path(..., description="Bangumi ID"),
):
    """
    获取番剧所有集数的可用性状态
    用于显示集数网格，标明哪些集数有资源
    """
    try:
        with get_session() as session:
            anime_repo = AnimeRepository(session)
            resource_repo = ResourceRepository(session)

            # 查找bangumi_id对应的anime
            anime = anime_repo.get_by_bangumi_id(bangumi_id)
            if not anime:
                raise HTTPException(
                    status_code=404, detail=f"未找到 bangumi_id={bangumi_id} 的番剧"
                )
            mikan_id = int(anime.mikan_id or 0)

            # 获取每集的资源统计
            availability_data = resource_repo.count_by_episode(mikan_id)

            episodes = {}
            for item in availability_data:
                episodes[str(item["episode_number"])] = {
                    "available": True,
                    "resource_count": item["resource_count"],
                }

            data = {"bangumi_id": bangumi_id, "episodes": episodes}

            return EpisodeAvailabilityResponse(
                success=True, message="获取集数可用性成功", data=data
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集数可用性失败: {str(e)}")


@router.get(
    "/search",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def search_anime_library(
    q: str = Query(..., description="搜索关键词", min_length=1),
    page: int = Query(1, description="页码", ge=1),
    limit: int = Query(12, description="每页数量", ge=1, le=50),
):
    """
    资源库搜索接口
    根据番剧名称模糊搜索，返回bangumi_id列表和分页信息
    """
    try:
        with get_session() as session:
            anime_repo = AnimeRepository(session)
            offset = (page - 1) * limit
            # 执行搜索
            search_result = anime_repo.search_by_title(q, limit, offset)
            # 提取bangumi_id列表
            bangumi_ids = [
                anime.bangumi_id
                for anime in search_result
                if getattr(anime, "bangumi_id", None)
            ]
            # 统计总数
            total = len(anime_repo.search_by_title(q, 1000000, 0))
            total_pages = (total + limit - 1) // limit
            pagination = {
                "current_page": page,
                "per_page": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
            return {
                "success": True,
                "message": f"搜索到 {len(bangumi_ids)} 个结果",
                "data": {"bangumi_ids": bangumi_ids, "pagination": pagination},
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
