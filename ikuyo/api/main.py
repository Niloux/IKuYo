#!/usr/bin/env python3
"""
FastAPI主应用
IKuYo动漫资源查询API
专注于资源获取场景
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ikuyo.api.routes import bangumi, health, resources
from ikuyo.core.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# 创建FastAPI应用实例
app = FastAPI(
    title="IKuYo动漫资源API",
    description="专注于资源获取的简洁API服务，与Bangumi API配合使用",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, prefix="/api/v1")
app.include_router(resources.router, prefix="/api/v1")
app.include_router(bangumi.router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    API根路径
    返回基本信息
    """
    return {
        "service": "IKuYo动漫资源API",
        "version": "2.0.0",
        "description": "专注于资源获取的简洁API服务",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "core_endpoints": [
            "/api/v1/animes/calendar",
            "/api/v1/animes/{id}",
            "/api/v1/animes/{id}/episodes",
            "/api/v1/animes/{id}/resources",
            "/api/v1/animes/search",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ikuyo.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["ikuyo"],
        log_level="info",
    )
