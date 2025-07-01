#!/usr/bin/env python3
"""
API数据模型
专注于资源获取场景的简洁设计
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

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


# =============== Bangumi章节模型 ===============


class BangumiEpisode(BaseModel):
    """Bangumi章节信息模型"""

    id: int = Field(..., description="章节ID")
    type: int = Field(..., description="章节类型(0:正片, 1:SP, 2:OP, 3:ED, 4:PV, 5:MAD, 6:其他)")
    name: str = Field(..., description="章节名称")
    name_cn: str = Field(..., description="章节中文名称")
    sort: float = Field(..., description="章节排序")
    ep: Optional[float] = Field(None, description="章节编号")
    airdate: Optional[str] = Field(None, description="播出日期")
    comment: int = Field(0, description="评论数")
    duration: str = Field("", description="时长")
    desc: str = Field("", description="简介")
    disc: int = Field(0, description="碟片编号")
    duration_seconds: Optional[int] = Field(None, description="时长(秒)")


class BangumiEpisodesResponse(BaseResponse):
    """Bangumi章节列表响应模型"""

    data: List[BangumiEpisode] = Field(..., description="章节列表")
    total: int = Field(..., description="总章节数")


class CrawlerTaskCreate(BaseModel):
    mode: str
    year: Optional[int] = None
    season: Optional[str] = None
    start_url: Optional[str] = None
    limit: Optional[int] = None


class CrawlerTaskResponse(BaseModel):
    id: Optional[int] = None
    status: str
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parameters: Any
    result_summary: Optional[Any] = None
    error_message: Optional[str] = None
    progress: Optional[Any] = None


class ScheduledJobCreate(BaseModel):
    job_id: str
    name: str
    cron_expression: str
    parameters: Any
    enabled: bool = True
    description: Optional[str] = None


class ScheduledJobUpdate(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    parameters: Optional[Any] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


class ScheduledJobResponse(BaseModel):
    id: Optional[int] = None
    job_id: str
    name: str
    cron_expression: str
    parameters: Any
    enabled: bool
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
