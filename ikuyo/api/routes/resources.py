#!/usr/bin/env python3
"""
资源API路由
专注于资源获取场景的简洁设计
"""

import time
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Path

from ikuyo.api.models.schemas import (
    AnimeProgressResponse,
    EpisodeAvailabilityResponse,
    EpisodeResourcesResponse,
    ErrorResponse,
    SubtitleGroupData,
    SubtitleGroupResource,
)
from ikuyo.core.database import DatabaseManager

router = APIRouter(prefix="/animes", tags=["Resources"])


def get_db_manager():
    """获取数据库管理器"""
    return DatabaseManager()


def get_subtitle_type_priority(subtitle_type: str) -> int:
    """获取字幕类型优先级（数字越小优先级越高）"""
    priority_map = {
        "中日双语": 1,
        "双语字幕": 2,
        "CHS": 3,
        "简体内封": 4,
        "CHT": 5,
        "繁体内封": 6,
        "简繁内封": 7,
        "中文字幕": 8,
        "内嵌字幕": 9,
        "外挂字幕": 10,
        "无字幕": 11,
        "RAW": 12,
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
    "/bangumi/{bangumi_id}/progress",
    response_model=AnimeProgressResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_anime_progress(
    bangumi_id: int = Path(..., description="Bangumi ID"),
    db: DatabaseManager = Depends(get_db_manager),
):
    """
    获取番剧更新进度
    返回最新集数、可用集数列表、字幕组信息等
    """
    try:
        # 根据bangumi_id获取mikan_id
        anime_query = "SELECT mikan_id, title FROM animes WHERE bangumi_id = ?"
        anime = db.execute_one(anime_query, (bangumi_id,))

        if not anime:
            raise HTTPException(status_code=404, detail=f"未找到 bangumi_id={bangumi_id} 的番剧")

        mikan_id = anime["mikan_id"]

        # 获取最新集数和可用集数
        progress_query = """
        SELECT 
            MAX(episode_number) as latest_episode,
            COUNT(DISTINCT episode_number) as available_episode_count,
            COUNT(*) as total_resources
        FROM resources 
        WHERE mikan_id = ? AND episode_number IS NOT NULL
        """
        progress = db.execute_one(progress_query, (mikan_id,))

        # 获取可用集数列表
        episodes_query = """
        SELECT DISTINCT episode_number 
        FROM resources 
        WHERE mikan_id = ? AND episode_number IS NOT NULL
        ORDER BY episode_number
        """
        episodes_data = db.execute_query(episodes_query, (mikan_id,))
        available_episodes = [ep["episode_number"] for ep in episodes_data]

        # 获取字幕组信息
        subtitle_groups_query = """
        SELECT DISTINCT sg.name
        FROM resources r
        JOIN subtitle_groups sg ON r.subtitle_group_id = sg.id
        WHERE r.mikan_id = ?
        ORDER BY sg.name
        """
        groups_data = db.execute_query(subtitle_groups_query, (mikan_id,))
        subtitle_groups = [group["name"] for group in groups_data]

        # 获取最后更新时间
        last_update_query = """
        SELECT MAX(release_date) as last_updated
        FROM resources 
        WHERE mikan_id = ?
        """
        last_update = db.execute_one(last_update_query, (mikan_id,))

        data = {
            "bangumi_id": bangumi_id,
            "latest_episode": progress["latest_episode"] if progress else 0,
            "available_episodes": available_episodes,
            "total_resources": progress["total_resources"] if progress else 0,
            "subtitle_groups": subtitle_groups,
            "last_updated": (
                datetime.fromtimestamp(last_update["last_updated"]).isoformat()
                if last_update and last_update["last_updated"]
                else None
            ),
        }

        return AnimeProgressResponse(success=True, message="获取番剧进度成功", data=data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取番剧进度失败: {str(e)}")


@router.get(
    "/bangumi/{bangumi_id}/episodes/{episode}/resources",
    response_model=EpisodeResourcesResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_episode_resources(
    bangumi_id: int = Path(..., description="Bangumi ID"),
    episode: int = Path(..., description="集数"),
    db: DatabaseManager = Depends(get_db_manager),
):
    """
    获取特定集数的资源
    按字幕组分类展示，每个字幕组内按偏好排序
    """
    try:
        # 根据bangumi_id获取mikan_id
        anime_query = "SELECT mikan_id FROM animes WHERE bangumi_id = ?"
        anime = db.execute_one(anime_query, (bangumi_id,))

        if not anime:
            raise HTTPException(status_code=404, detail=f"未找到 bangumi_id={bangumi_id} 的番剧")

        mikan_id = anime["mikan_id"]

        # 获取该集数的所有资源
        resources_query = """
        SELECT 
            r.id, r.title, r.resolution, r.subtitle_type, r.file_size,
            r.magnet_url, r.torrent_url, r.release_date,
            sg.id as subtitle_group_id, sg.name as subtitle_group_name
        FROM resources r
        JOIN subtitle_groups sg ON r.subtitle_group_id = sg.id
        WHERE r.mikan_id = ? AND r.episode_number = ?
        ORDER BY sg.name
        """
        resources_data = db.execute_query(resources_query, (mikan_id, episode))

        if not resources_data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到番剧 {bangumi_id} 第 {episode} 集的资源",
            )

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
                    get_subtitle_type_priority(x.subtitle_type),
                    get_resolution_priority(x.resolution),
                    -(
                        int(
                            time.mktime(
                                datetime.fromisoformat(
                                    x.release_date.replace("Z", "+00:00")
                                ).timetuple()
                            )
                        )
                        if x.release_date
                        else 0
                    ),
                )
            )

        # 转换为列表格式
        subtitle_groups_list = [
            SubtitleGroupData(**group_data) for group_data in subtitle_groups.values()
        ]

        data = {
            "bangumi_id": bangumi_id,
            "episode": episode,
            "total_resources": len(resources_data),
            "subtitle_groups": [group.dict() for group in subtitle_groups_list],
        }

        return EpisodeResourcesResponse(
            success=True, message=f"获取第 {episode} 集资源成功", data=data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集数资源失败: {str(e)}")


@router.get(
    "/bangumi/{bangumi_id}/episodes/availability",
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
