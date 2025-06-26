#!/usr/bin/env python3
"""
Bangumi API路由
专注于两个核心业务：每日放送和番剧详情
"""

from fastapi import APIRouter, HTTPException, Path

from ikuyo.api.models.schemas import (
    BangumiCalendarResponse,
    BangumiSubjectResponse,
    ErrorResponse,
)
from ikuyo.core.bangumi_service import bangumi_service

router = APIRouter(prefix="/bangumi", tags=["Bangumi"])


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
        calendar_data = bangumi_service.get_calendar()

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
        subject_data = bangumi_service.get_subject_info(bangumi_id)

        if subject_data is None:
            raise HTTPException(
                status_code=404, detail=f"未找到 bangumi_id={bangumi_id} 的番剧详情"
            )

        return BangumiSubjectResponse(success=True, message="获取番剧详情成功", data=subject_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取番剧详情失败: {str(e)}")
