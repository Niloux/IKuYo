#!/usr/bin/env python3
"""
FastAPI主应用
IKuYo动漫资源查询API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ikuyo.api.routes import animes, health, resources

# 创建FastAPI应用实例
app = FastAPI(
    title="IKuYo动漫资源API",
    description="基于Mikan Project的动漫资源查询API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
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
app.include_router(animes.router, prefix="/api/v1")
app.include_router(resources.router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    API根路径
    返回基本信息
    """
    return {
        "service": "IKuYo动漫资源API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
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
