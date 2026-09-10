import os
import sys

# 将工作目录固定为本文件所在目录，保证在任意目录下启动时 .env.*、logs、vf_admin 等相对路径都能正确解析
BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(BACKEND_ROOT)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

import uvicorn  # noqa: E402

from config.env import AppConfig  # noqa: E402
from server import create_app

if __name__ != '__main__':
    app = create_app()

if __name__ == '__main__':
    uvicorn.run(
        app='server:create_app',
        host=AppConfig.app_host,
        port=AppConfig.app_port,
        root_path=AppConfig.app_root_path,
        reload=AppConfig.app_reload,
        workers=AppConfig.app_workers,
        factory=True,
    )
