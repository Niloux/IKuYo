import os
import sys

# 自动切换到项目根目录（包含ikuyo/的目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from twisted.internet import asyncioreactor

asyncioreactor.install()

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "ikuyo.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["ikuyo"],
        log_level="info",
        loop="asyncio",
    )
