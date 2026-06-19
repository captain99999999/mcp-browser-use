#!/usr/bin/env python3
"""直接在 winserver 上测试 web_search 和 web_fetch 功能"""

import sys

sys.path.insert(0, r"D:\browser-projects\mcp-browser-use\src")

import asyncio
import json


async def test_web_search():
    """测试 web_search 函数"""
    print("=" * 60)
    print("测试 web_search 功能")
    print("=" * 60)

    try:
        from mcp_server_browser_use.server import web_search

        result = await web_search(query="Python asyncio", max_results=3, max_queries=2)

        print(f"\n返回结果类型: {type(result)}")
        print(f"结果长度: {len(result)} 字符")

        # 尝试解析为 JSON
        try:
            results = json.loads(result)
            print(f"\n搜索结果（共 {len(results)} 条）:")
            for i, item in enumerate(results[:3]):
                title = item.get("title", "未知")
                url = item.get("url", "未知")
                snippet = item.get("snippet", "无描述")[:60]
                print(f"\n  {i + 1}. {title}")
                print(f"     URL: {url}")
                print(f"     摘要: {snippet}...")
            return True
        except json.JSONDecodeError:
            print(f"\n原始结果（前500字符）:\n{result[:500]}...")
            return False

    except Exception as e:
        print(f"错误: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_web_fetch():
    """测试 web_fetch 函数"""
    print("\n" + "=" * 60)
    print("测试 web_fetch 功能")
    print("=" * 60)

    try:
        from mcp_server_browser_use.server import web_fetch

        result = await web_fetch(url="https://github.com/Saik0s/mcp-browser-use", timeout=30)

        print(f"\n返回结果类型: {type(result)}")
        print(f"结果长度: {len(result)} 字符")

        # 检查内容
        if "mcp-browser-use" in result.lower():
            print("\n✅ 内容验证通过: 包含 'mcp-browser-use'")
            print(f"\n内容预览（前500字符）:\n{result[:500]}...")
            return True
        else:
            print("\n⚠️  内容验证失败: 未找到预期的关键字")
            return False

    except Exception as e:
        print(f"错误: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    print("开始测试 Web 工具...")
    print(f"工作目录: {sys.path[0]}\n")

    test1 = await test_web_search()
    test2 = await test_web_fetch()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"web_search: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"web_fetch:  {'✅ 通过' if test2 else '❌ 失败'}")

    if test1 and test2:
        print("\n所有测试通过 ✅")
        return 0
    else:
        print("\n部分测试失败 ❌")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
