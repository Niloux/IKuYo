#!/usr/bin/env python3
"""
Bangumi API路由
专注于两个核心业务：每日放送和番剧详情
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from ikuyo.api.models.schemas import (
    BangumiCalendarResponse,
    BangumiEpisode,
    BangumiEpisodesResponse,
    BangumiSubjectResponse,
    ErrorResponse,
)
from ikuyo.core.bangumi_service import BangumiService

router = APIRouter(prefix="/bangumi", tags=["Bangumi"])

# 创建BangumiService实例
bangumi_service = BangumiService()


@router.get(
    "/calendar",
    response_model=BangumiCalendarResponse,
    responses={500: {"model": ErrorResponse}},
)
async def get_bangumi_calendar():
    """
    获取每日放送
    为首页提供新番时间表
    """
    try:
        calendar_data = await bangumi_service.get_calendar()

        if calendar_data is None:
            raise HTTPException(status_code=500, detail="获取每日放送数据失败")

        return BangumiCalendarResponse(
            success=True, message="获取每日放送成功", data=calendar_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取每日放送失败: {str(e)}")


@router.get(
    "/subjects/{bangumi_id}",
    response_model=BangumiSubjectResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_bangumi_subject(
    bangumi_id: int = Path(..., description="Bangumi ID"),
):
    """
    获取番剧详情
    为详情页提供元数据补充
    """
    try:
        subject_data = await bangumi_service.get_subject(bangumi_id)

        if subject_data is None:
            raise HTTPException(
                status_code=404, detail=f"未找到 bangumi_id={bangumi_id} 的番剧详情"
            )

        return BangumiSubjectResponse(success=True, message="获取番剧详情成功", data=subject_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取番剧详情失败: {str(e)}")


@router.get(
    "/subjects/{subject_id}/episodes",
    response_model=BangumiEpisodesResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_bangumi_episodes(
    subject_id: int = Path(..., description="番剧subject_id"),
    episode_type: Optional[int] = Query(
        None, description="章节类型筛选 (0:正片, 1:SP, 2:OP, 3:ED, 4:PV, 6:其他)"
    ),
    limit: int = Query(100, description="返回数量限制", ge=1, le=1000),
    offset: int = Query(0, description="偏移量", ge=0),
):
    """
    获取番剧章节信息
    支持分页和筛选，对长篇动画至关重要
    """
    try:
        episodes_data = await bangumi_service.get_episodes(
            subject_id=subject_id, episode_type=episode_type, limit=limit, offset=offset
        )

        if episodes_data is None:
            raise HTTPException(
                status_code=404, detail=f"未找到 subject_id={subject_id} 的章节信息"
            )

        # 转换数据格式以匹配响应模型
        episodes_list = episodes_data.get("data", [])
        total = episodes_data.get("total", 0)

        # 转换为BangumiEpisode模型
        episode_models = []
        for ep_data in episodes_list:
            try:
                episode_models.append(BangumiEpisode(**ep_data))
            except Exception as e:
                print(f"转换章节数据失败: {e}, 数据: {ep_data}")
                continue

        return BangumiEpisodesResponse(
            success=True, message="获取章节信息成功", data=episode_models, total=total
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取章节信息失败: {str(e)}")
