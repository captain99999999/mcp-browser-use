#!/usr/bin/env python
"""Start the mcp-browser-use service with its own virtualenv."""

import logging
import os
import sys
from pathlib import Path

# 让服务启动时优先读取部署机上的 .env 文件
os.environ.setdefault("MCP_BROWSER_USE_ENV_FILE", r"D:\browser-projects\use-browser\.env")

# 设置 PYTHONPATH 指向 mcp-browser-use 的 src 目录
sys.path.insert(0, r"D:\browser-projects\mcp-browser-use\src")

from mcp_server_browser_use.config import settings
from mcp_server_browser_use.server import serve

# 配置日志持久化到文件
log_file = Path(r"D:\browser-projects\mcp-browser-use\logs\server.log")
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

print("Starting mcp-browser-use server...")
print(f"  LLM: {settings.llm.provider}/{settings.llm.model_name}")
print(f"  API Key: {'loaded' if settings.llm.get_api_key_for_provider() else 'missing'}")
print(f"  CDP:  {settings.browser.cdp_url}")
print(f"  HTTP: http://{settings.server.host}:{settings.server.port}/mcp")
print(f"  Log:  {log_file}")
print()

logger.info("Starting mcp-browser-use server with browser pool...")

try:
    server = serve()
    server.run(transport="streamable-http", host=settings.server.host, port=settings.server.port)
except KeyboardInterrupt:
    logger.info("Server received KeyboardInterrupt, shutting down...")
except Exception as e:
    logger.error(f"Server failed: {e}", exc_info=True)
    raise
