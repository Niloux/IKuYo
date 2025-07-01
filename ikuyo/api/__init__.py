"""
API模块 - 提供RESTful接口查询数据库
基于FastAPI框架，提供动画和资源的查询功能
"""

from .app import app

__all__ = ["app"]
