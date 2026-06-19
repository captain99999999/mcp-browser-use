#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mcp-browser-use 服务启动脚本（使用 mcp-browser-use 自身的 venv）
此脚本的启动脚本，不再使用 use-browser 的 venv，直接使用 mcp-browser-use 自身的 venv。
"""
import asyncio
import os
import sys
from pathlib import Path

# 设置 PYTHONPATH 指向 mcp-browser-use 的 src 目录
sys.path.insert(0, r"D:\browser-projects\mcp-browser-use\src")

from mcp_server_browser_use.server import serve
from mcp_server_browser_use.config import settings

print(f"Starting mcp-browser-use server...")
print(f"  LLM: {settings.llm.provider}/{settings.llm.model_name}")
print(f"  CDP:  {settings.browser.cdp_url}")
print(f"  HTTP: http://{settings.server.host}:{settings.server.port}/mcp")
print()

server = serve()
server.run(transport="streamable-http", host=settings.server.host, port=settings.server.port)