#!/usr/bin/env python3
"""
API数据模型
专注于资源获取场景的简洁设计
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# =============== 基础响应模型 ===============


class BaseResponse(BaseModel):
    """基础响应模型"""

    success: bool = Field(True, description="操作是否成功")
    message: str = Field("操作成功", description="响应消息")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    success: bool = Field(False, description="操作是否成功")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")


# =============== 核心业务模型 ===============


class AnimeProgressResponse(BaseResponse):
    """番剧更新进度响应模型"""

    data: dict = Field(..., description="更新进度数据")


class SubtitleGroupResource(BaseModel):
    """字幕组资源模型"""

    id: int = Field(..., description="资源ID")
    title: str = Field(..., description="资源标题")
    resolution: Optional[str] = Field(None, description="分辨率")
    subtitle_type: Optional[str] = Field(None, description="字幕类型")
    file_size: Optional[str] = Field(None, description="文件大小")
    magnet_url: Optional[str] = Field(None, description="磁力链接")
    torrent_url: Optional[str] = Field(None, description="种子链接")
    release_date: Optional[str] = Field(None, description="发布时间")

    class Config:
        from_attributes = True


class SubtitleGroupData(BaseModel):
    """字幕组数据模型"""

    id: int = Field(..., description="字幕组ID")
    name: str = Field(..., description="字幕组名称")
    resource_count: int = Field(..., description="该集资源数量")
    resources: List[SubtitleGroupResource] = Field(..., description="资源列表")


class EpisodeResourcesResponse(BaseResponse):
    """集数资源响应模型"""

    data: dict = Field(..., description="集数资源数据")


class EpisodeAvailabilityResponse(BaseResponse):
    """集数可用性响应模型"""

    data: dict = Field(..., description="集数可用性数据")


# =============== Bangumi API模型 ===============


class BangumiCalendarResponse(BaseResponse):
    """Bangumi每日放送响应模型"""

    data: List[dict] = Field(..., description="每日放送数据")


class BangumiSubjectResponse(BaseResponse):
    """Bangumi番剧详情响应模型"""

    data: dict = Field(..., description="番剧详情数据")


# =============== 健康检查模型 ===============


class HealthResponse(BaseModel):
    """健康检查响应模型"""

    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API版本")
    timestamp: str = Field(..., description="检查时间")
    database_status: str = Field(..., description="数据库状态")
    cache_stats: Optional[Dict[str, Any]] = Field(None, description="缓存统计信息")
