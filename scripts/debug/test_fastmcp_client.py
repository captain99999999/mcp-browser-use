#!/usr/bin/env python3
"""用 FastMCP Client 测试 winserver 服务连通性"""

import asyncio
import sys


async def test_connection():
    """测试 MCP 服务连接"""
    from fastmcp import Client

    url = "http://192.168.110.250:8383/mcp"
    print(f"连接到 MCP 服务: {url}\n")

    try:
        async with Client(url, timeout=30) as client:
            # 列出所有工具
            print("=" * 60)
            print("获取工具列表")
            print("=" * 60)
            tools = await client.list_tools()
            print(f"找到 {len(tools.tools)} 个工具\n")

            web_tools = [t for t in tools.tools if t.name.startswith("web_")]
            if web_tools:
                print("Web 相关工具:")
                for t in web_tools:
                    print(f"  - {t.name}: {t.description[:60]}...\n")
            else:
                print("❌ 未找到 web_* 工具\n")
                return False

            # 测试 web_search
            print("=" * 60)
            print("测试 web_search")
            print("=" * 60)
            result = await client.call_tool("web_search", {"query": "Python", "max_results": 3, "max_queries": 1})

            if result.is_error:
                print(f"❌ web_search 失败: {result.content}")
                return False

            content = result.content[0].text if result.content else ""
            print("✅ web_search 成功\n")
            print(f"响应长度: {len(content)} 字符")
            print(f"响应预览（前200字符）:\n{content[:200]}...\n")

            return True

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
