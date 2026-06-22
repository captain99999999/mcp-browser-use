#!/usr/bin/env python3
# ruff: noqa: RUF001, RUF003
"""Validate anti-detection behavior using FastMCP streamable HTTP client."""

import asyncio
import sys
import time
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

WIN_SERVER_URL = "http://192.168.110.250:8383/mcp"


def _response_text(response: Any) -> str:
    """Return plain text from FastMCP tool response for keyword checks."""
    if hasattr(response, "content") and response.content:
        fragments: list[str] = []
        for item in response.content:
            if hasattr(item, "text") and item.text:
                fragments.append(str(item.text))
            else:
                fragments.append(str(item))
        return "\n".join(fragments)
    return str(response)


async def test_service_health() -> bool:
    """测试 1: 服务健康检查"""
    print("=" * 70)
    print("测试 1: 服务健康检查")
    print("=" * 70)
    try:
        client = Client(StreamableHttpTransport(url=WIN_SERVER_URL))
        async with client:
            tools = await client.list_tools()
            print("✅ 服务运行正常")
            print(f"   可用工具数: {len(tools)}")
            print(f"   工具列表: {[tool.name for tool in tools]}")
            return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


async def test_google_search(query: str, test_name: str) -> tuple[bool, bool, float]:
    """测试 Google 搜索是否触发 CAPTCHA"""
    print(f"\n{'=' * 70}")
    print(f"测试 {test_name}: Google 搜索 - '{query}'")
    print("=" * 70)

    start_time = time.time()
    try:
        client = Client(StreamableHttpTransport(url=WIN_SERVER_URL))
        async with client:
            result = await client.call_tool("web_search", {"query": query, "max_results": 5})

            elapsed = time.time() - start_time
            print(f"\n响应时间: {elapsed:.2f}s")
            print("✅ 搜索成功!")

            search_text = _response_text(result)

            # 检查响应中是否有 CAPTCHA 迹象
            response_lower = search_text.lower()
            captcha_indicators = ["captcha", "robot", "not a robot", "human verification", "recaptcha", "bot", "verify you're human"]
            found_captcha = any(indicator in response_lower for indicator in captcha_indicators)

            if found_captcha:
                print("⚠️  警告: 检测到可能的 CAPTCHA/机器人检测内容")
                print("这可能表明反爬虫措施未完全生效")
            else:
                print("✅ 未检测到 CAPTCHA 内容")

            # 显示搜索结果摘要
            print(f"\n返回内容长度: {len(search_text)} 字符")
            print(f"返回内容预览:\n{search_text[:300]}...")

            has_content = len(search_text.strip()) > 0
            return has_content, not found_captcha, elapsed

    except TimeoutError:
        elapsed = time.time() - start_time
        print(f"❌ 请求超时 ({elapsed:.2f}s)")
        return False, False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 请求异常: {e}")
        return False, False, elapsed


async def main() -> None:
    print("\n" + "=" * 70)
    print("🦸 mcp-browser-use 反爬虫功能验证测试")
    print("=" * 70)
    print(f"目标服务器: {WIN_SERVER_URL}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 测试 1: 健康检查
    if not await test_service_health():
        print("\n❌ 服务不可用，无法继续测试")
        sys.exit(1)

    # 等待服务稳定
    print("\n等待 3 秒让服务稳定...")
    await asyncio.sleep(3)

    # 测试 2-6: 多个查询测试
    test_queries = [
        ("Python tutorial", "2"),
        ("best laptop 2025", "3"),
        ("how to use Docker", "4"),
        ("machine learning basics", "5"),
        ("VSCode extensions", "6"),
    ]

    results = []
    total_time = 0

    for query, test_name in test_queries:
        success, no_captcha, elapsed = await test_google_search(query, test_name)
        results.append({"query": query, "success": success, "no_captcha": no_captcha, "elapsed": elapsed})
        total_time += elapsed

        # 测试间隔，避免过于频繁
        print("\n等待 5 秒后进行下一个查询...")
        await asyncio.sleep(5)

    # 生成最终报告
    print("\n" + "=" * 70)
    print("📊 最终测试报告")
    print("=" * 70)

    success_count = sum(1 for r in results if r["success"])
    captcha_count = sum(1 for r in results if r["no_captcha"])
    total_count = len(results)

    print(f"\n查询总数: {total_count}")
    print(f"成功: {success_count}/{total_count} ({success_count / total_count * 100:.1f}%)")
    print(f"未触发 CAPTCHA: {captcha_count}/{total_count} ({captcha_count / total_count * 100:.1f}%)")
    print(f"平均响应时间: {total_time / total_count:.2f}s")

    print("\n详细结果:")
    print("-" * 70)
    for i, r in enumerate(results, 1):
        status = "✅" if r["success"] else "❌"
        bot_status = "✅ 无 CAPTCHA" if r["no_captcha"] else ("⚠️ 有 CAPTCHA" if r["success"] else "N/A")
        print(f"{i}. {status} '{r['query']}' - {r['elapsed']:.2f}s - {bot_status}")

    print("\n" + "=" * 70)
    if success_count == total_count and captcha_count == total_count:
        print("✅ 所有测试通过！反爬虫功能正常工作")
        sys.exit(0)
    elif success_count == total_count:
        print("⚠️  所有查询成功，但部分检测到 CAPTCHA 内容")
        print("建议检查浏览器会话和反爬虫配置")
        sys.exit(1)
    else:
        print("❌ 部分或全部测试失败，请检查日志")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
