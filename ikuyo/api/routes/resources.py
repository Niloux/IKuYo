#!/usr/bin/env python3
"""
资源API路由
专注于资源获取场景的简洁设计
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from ikuyo.api.models.schemas import (
    EpisodeAvailabilityResponse,
    EpisodeResourcesResponse,
    ErrorResponse,
    SubtitleGroupData,
    SubtitleGroupResource,
)
from ikuyo.core.database import DatabaseManager

router = APIRouter(prefix="/animes", tags=["Resources"])


# 创建全局数据库管理器实例
_db_manager = DatabaseManager()


def get_db_manager():
    """获取数据库管理器"""
    return _db_manager


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
async def get_anime_resources(
    bangumi_id: int = Path(..., description="Bangumi ID"),
    episode: Optional[int] = Query(None, description="指定集数，不提供则返回所有集数"),
    resolution: Optional[str] = Query(None, description="分辨率筛选"),
    subtitle_type: Optional[str] = Query(None, description="字幕类型筛选"),
    limit: int = Query(100, description="返回数量限制", ge=1, le=500),
    offset: int = Query(0, description="偏移量", ge=0),
    db: DatabaseManager = Depends(get_db_manager),
):
    """
    统一的资源接口
    支持获取特定集数的资源或全番剧资源，按字幕组分类展示
    """
    try:
        # 根据bangumi_id获取mikan_id
        anime_query = "SELECT mikan_id, title FROM animes WHERE bangumi_id = ?"
        anime = db.execute_one(anime_query, (bangumi_id,))

        if not anime:
            raise HTTPException(status_code=404, detail=f"未找到 bangumi_id={bangumi_id} 的番剧")

        mikan_id = anime["mikan_id"]

        # 构建筛选条件
        conditions = ["r.mikan_id = ?"]
        params = [mikan_id]

        if episode is not None:
            conditions.append("r.episode_number = ?")
            params.append(episode)

        if resolution:
            conditions.append("r.resolution = ?")
            params.append(resolution)

        if subtitle_type:
            conditions.append("r.subtitle_type = ?")
            params.append(subtitle_type)

        where_clause = " AND ".join(conditions)

        # 获取资源
        resources_query = f"""
        SELECT 
            r.id, r.title, r.episode_number, r.resolution, r.subtitle_type, r.file_size,
            r.magnet_url, r.torrent_url, r.release_date,
            sg.id as subtitle_group_id, sg.name as subtitle_group_name
        FROM resources r
        JOIN subtitle_groups sg ON r.subtitle_group_id = sg.id
        WHERE {where_clause}
        ORDER BY sg.name, r.episode_number, r.release_date DESC
        LIMIT ? OFFSET ?
        """
        resources_data = db.execute_query(resources_query, tuple(params + [limit, offset]))

        # 获取总数统计
        count_query = f"""
        SELECT COUNT(*) as total
        FROM resources r
        JOIN subtitle_groups sg ON r.subtitle_group_id = sg.id
        WHERE {where_clause}
        """
        count_result = db.execute_one(count_query, tuple(params))
        total_resources = count_result["total"] if count_result else 0

        if not resources_data:
            if episode is not None:
                error_msg = f"未找到番剧 {bangumi_id} 第 {episode} 集的资源"
            else:
                error_msg = "该番剧暂无可用资源"

            data = {
                "bangumi_id": bangumi_id,
                "episode": episode,
                "total_resources": 0,
                "subtitle_groups": [],
                "filters": {"resolution": resolution, "subtitle_type": subtitle_type},
                "pagination": {"limit": limit, "offset": offset, "total": total_resources},
            }
            return EpisodeResourcesResponse(success=True, message=error_msg, data=data)

        # 按字幕组分类
        subtitle_groups: Dict[int, Dict] = {}
        for resource in resources_data:
            group_id = resource["subtitle_group_id"]
            group_name = resource["subtitle_group_name"]

            if group_id not in subtitle_groups:
                subtitle_groups[group_id] = {
                    "id": group_id,
                    "name": group_name,
                    "resource_count": 0,
                    "resources": [],
                }

            # 创建资源对象
            resource_obj = SubtitleGroupResource(
                id=resource["id"],
                title=resource["title"],
                resolution=resource["resolution"],
                subtitle_type=resource["subtitle_type"],
                file_size=resource["file_size"],
                magnet_url=resource["magnet_url"],
                torrent_url=resource["torrent_url"],
                release_date=(
                    datetime.fromtimestamp(resource["release_date"]).isoformat()
                    if resource["release_date"]
                    else None
                ),
            )

            subtitle_groups[group_id]["resources"].append(resource_obj)
            subtitle_groups[group_id]["resource_count"] += 1

        # 对每个字幕组内的资源进行排序
        for group_data in subtitle_groups.values():
            group_data["resources"].sort(
                key=lambda x: (
                    # 先按集数排序（如果有多集）
                    int(x.title.split("第")[-1].split("集")[0])
                    if "第" in x.title and "集" in x.title
                    else 999,
                    # 再按字幕类型优先级
                    get_subtitle_type_priority(x.subtitle_type),
                    # 最后按分辨率优先级
                    get_resolution_priority(x.resolution),
                )
            )

        # 转换为列表格式
        subtitle_groups_list = [
            SubtitleGroupData(**group_data) for group_data in subtitle_groups.values()
        ]

        data = {
            "bangumi_id": bangumi_id,
            "episode": episode,
            "total_resources": total_resources,
            "subtitle_groups": [group.dict() for group in subtitle_groups_list],
            "filters": {"resolution": resolution, "subtitle_type": subtitle_type},
            "pagination": {"limit": limit, "offset": offset, "total": total_resources},
        }

        if episode is not None:
            message = f"获取第 {episode} 集资源成功"
        else:
            message = f"获取番剧资源成功，共找到 {total_resources} 个资源"

        return EpisodeResourcesResponse(success=True, message=message, data=data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集数资源失败: {str(e)}")


@router.get(
    "/{bangumi_id}/episodes/availability",
    response_model=EpisodeAvailabilityResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_episodes_availability(
    bangumi_id: int = Path(..., description="Bangumi ID"),
    db: DatabaseManager = Depends(get_db_manager),
):
    """
    获取番剧所有集数的可用性状态
    用于显示集数网格，标明哪些集数有资源
    """
    try:
        # 根据bangumi_id获取mikan_id
        anime_query = "SELECT mikan_id FROM animes WHERE bangumi_id = ?"
        anime = db.execute_one(anime_query, (bangumi_id,))

        if not anime:
            raise HTTPException(status_code=404, detail=f"未找到 bangumi_id={bangumi_id} 的番剧")

        mikan_id = anime["mikan_id"]

        # 获取每集的资源统计
        availability_query = """
        SELECT 
            episode_number,
            COUNT(*) as resource_count
        FROM resources 
        WHERE mikan_id = ? AND episode_number IS NOT NULL
        GROUP BY episode_number
        ORDER BY episode_number
        """
        availability_data = db.execute_query(availability_query, (mikan_id,))

        episodes = {}
        for item in availability_data:
            episodes[str(item["episode_number"])] = {
                "available": True,
                "resource_count": item["resource_count"],
            }

        data = {"bangumi_id": bangumi_id, "episodes": episodes}

        return EpisodeAvailabilityResponse(success=True, message="获取集数可用性成功", data=data)

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
    db: DatabaseManager = Depends(get_db_manager),
):
    """
    资源库搜索接口
    根据番剧名称模糊搜索，返回bangumi_id列表和分页信息
    """
    try:
        from ikuyo.core.database import AnimeRepository

        anime_repo = AnimeRepository(db)

        # 计算offset
        offset = (page - 1) * limit

        # 执行搜索
        search_result = anime_repo.search_animes_by_title_with_pagination(q, limit, offset)

        # 提取bangumi_id列表
        bangumi_ids = [
            anime["bangumi_id"] for anime in search_result["animes"] if anime["bangumi_id"]
        ]

        # 构建分页信息
        pagination = {
            "current_page": page,
            "per_page": limit,
            "total": search_result["total"],
            "total_pages": (search_result["total"] + limit - 1) // limit,
            "has_next": search_result["has_next"],
            "has_prev": search_result["has_prev"],
        }

        return {
            "success": True,
            "message": f"搜索到 {len(bangumi_ids)} 个结果",
            "data": {"bangumi_ids": bangumi_ids, "pagination": pagination},
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
