#!/usr/bin/env python3
"""
API数据模型
定义请求和响应的数据结构
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# =============== 基础模型 ===============


class PaginationResponse(BaseModel):
    """分页响应模型"""

    page: int = Field(..., description="当前页码")
    per_page: int = Field(..., description="每页数量")
    total: int = Field(..., description="总记录数")
    pages: int = Field(..., description="总页数")


class BaseResponse(BaseModel):
    """基础响应模型"""

    success: bool = Field(True, description="操作是否成功")
    message: str = Field("操作成功", description="响应消息")


class DataResponse(BaseResponse):
    """带数据的响应模型"""

    data: List[Any]


class PaginatedResponse(BaseResponse):
    """分页数据响应模型"""

    pagination: PaginationResponse
    data: List[Any]


# =============== 查询参数模型 ===============


class AnimeQueryParams(BaseModel):
    """动画查询参数"""

    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    q: Optional[str] = Field(None, description="搜索关键词")
    status: Optional[str] = Field(None, description="动画状态")


class ResourceQueryParams(BaseModel):
    """资源查询参数"""

    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    anime_id: Optional[int] = Field(None, description="动画ID")
    resolution: Optional[str] = Field(None, description="分辨率")
    episode: Optional[int] = Field(None, description="集数")


class SearchParams(BaseModel):
    """统一搜索参数"""

    type: str = Field(..., pattern="^(anime|resource)$", description="搜索类型")
    q: str = Field(..., min_length=1, description="搜索关键词")
    limit: int = Field(10, ge=1, le=50, description="结果数量限制")


# =============== 响应数据模型 ===============


class AnimeResponse(BaseModel):
    """动画响应模型"""

    mikan_id: int = Field(..., description="Mikan ID")
    bangumi_id: Optional[int] = Field(None, description="Bangumi ID")
    title: str = Field(..., description="动画标题")
    original_title: Optional[str] = Field(None, description="原始标题")
    broadcast_day: Optional[str] = Field(None, description="播出日期")
    broadcast_start: Optional[int] = Field(None, description="播出开始时间戳")
    official_website: Optional[str] = Field(None, description="官方网站")
    bangumi_url: Optional[str] = Field(None, description="Bangumi链接")
    description: Optional[str] = Field(None, description="描述")
    status: str = Field(..., description="状态")
    created_at: int = Field(..., description="创建时间戳")
    updated_at: int = Field(..., description="更新时间戳")

    class Config:
        from_attributes = True


class SubtitleGroupResponse(BaseModel):
    """字幕组响应模型"""

    id: int = Field(..., description="字幕组ID")
    name: str = Field(..., description="字幕组名称")
    is_subscribed: bool = Field(..., description="是否已订阅")


class ResourceResponse(BaseModel):
    """资源响应模型"""

    id: int = Field(..., description="资源ID")
    mikan_id: int = Field(..., description="动画ID")
    subtitle_group_id: int = Field(..., description="字幕组ID")
    episode_number: Optional[int] = Field(None, description="集数")
    title: str = Field(..., description="资源标题")
    file_size: Optional[str] = Field(None, description="文件大小")
    resolution: Optional[str] = Field(None, description="分辨率")
    subtitle_type: Optional[str] = Field(None, description="字幕类型")
    magnet_url: Optional[str] = Field(None, description="磁力链接")
    torrent_url: Optional[str] = Field(None, description="种子链接")
    play_url: Optional[str] = Field(None, description="播放链接")
    magnet_hash: Optional[str] = Field(None, description="磁力哈希")
    release_date: Optional[int] = Field(None, description="发布时间戳")
    created_at: int = Field(..., description="创建时间戳")
    updated_at: int = Field(..., description="更新时间戳")

    # 关联信息
    anime_title: Optional[str] = Field(None, description="动画标题")
    subtitle_group_name: Optional[str] = Field(None, description="字幕组名称")

    class Config:
        from_attributes = True


class AnimeDetailResponse(AnimeResponse):
    """动画详情响应模型（包含资源信息）"""

    resources: List[ResourceResponse] = Field(default_factory=list, description="相关资源")
    subtitle_groups: List[SubtitleGroupResponse] = Field(
        default_factory=list, description="字幕组列表"
    )


# =============== 统计响应模型 ===============


class StatsResponse(BaseModel):
    """统计信息响应模型"""

    total_animes: int = Field(..., description="动画总数")
    total_resources: int = Field(..., description="资源总数")
    total_subtitle_groups: int = Field(..., description="字幕组总数")
    latest_update: Optional[int] = Field(None, description="最新更新时间戳")


class HealthResponse(BaseModel):
    """健康检查响应模型"""

    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API版本")
    timestamp: int = Field(..., description="检查时间戳")
    database_status: str = Field(..., description="数据库状态")


# =============== 错误响应模型 ===============


class ErrorResponse(BaseModel):
    """错误响应模型"""

    success: bool = Field(False, description="操作是否成功")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
