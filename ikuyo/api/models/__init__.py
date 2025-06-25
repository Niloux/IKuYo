#!/usr/bin/env python3
"""
API数据模型包
"""

from .schemas import (
    AnimeProgressResponse,
    BaseResponse,
    EpisodeAvailabilityResponse,
    EpisodeResourcesResponse,
    ErrorResponse,
    HealthResponse,
    SubtitleGroupData,
    SubtitleGroupResource,
)

__all__ = [
    "BaseResponse",
    "ErrorResponse",
    "AnimeProgressResponse",
    "EpisodeResourcesResponse",
    "EpisodeAvailabilityResponse",
    "SubtitleGroupResource",
    "SubtitleGroupData",
    "HealthResponse",
]
