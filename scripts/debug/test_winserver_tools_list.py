#!/usr/bin/env python3
"""测试 winserver MCP 服务的 web_search 和 web_fetch 工具（正确格式）"""

import requests
import json
import sys

MCP_BASE_URL = "http://192.168.110.250:8383/mcp"


def list_tools():
    """获取 MCP 工具列表"""
    print("=" * 60)
    print("获取 MCP 工具列表")
    print("=" * 60)

    try:
        response = requests.get(f"{MCP_BASE_URL}/tools/list", timeout=10)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n响应结构: {result.keys()}")

            # 提取工具列表
            content = result.get("content", [])
            if content and isinstance(content[0], dict):
                tool_data = content[0]
                tool_list_text = tool_data.get("text", "无工具列表")

                # 尝试解析 JSON
                try:
                    tools = json.loads(tool_list_text)
                    print(f"\n找到 {len(tools)} 个工具\n")

                    web_tools_found = []
                    for tool in tools:
                        name = tool.get("name", "未知")
                        description = tool.get("description", "无描述")[:60]

                        # 查找 web 相关工具
                        if name.startswith("web_"):
                            web_tools_found.append(name)
                            print(f"✓ {name}: {description}...")

                    print(f"\n找到 web 相关工具: {', '.join(web_tools_found)}")
                    return web_tools_found
                except json.JSONDecodeError as e:
                    print(f"JSON 解析失败: {e}")
                    print(f"原始内容（前500字符）:\n{tool_list_text[:500]}")
            else:
                print("响应格式不符预期")
                print(f"原始响应: {result}")
        else:
            print(f"错误: HTTP {response.status_code}")
            print(response.text)

        return []

    except Exception as e:
        print(f"异常: {e}")
        import traceback

        traceback.print_exc()
        return []


def test_web_search():
    """测试 web_search 工具"""
    print("\n" + "=" * 60)
    print("测试 web_search 工具")
    print("=" * 60)

    payload = {"arguments": {"query": "Python asyncio", "max_results": 3, "max_queries": 2}}

    try:
        response = requests.post(
            f"{MCP_BASE_URL}/tools/web_search",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120,  # 给足够时间执行搜索
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n响应类型: {result.get('meta', {}).get('contentType', 'unknown')}")

            content = result.get("content", [])
            if content:
                result_text = content[0].get("text", "无响应")

                # 尝试解析为 JSON（搜索结果）
                try:
                    search_results = json.loads(result_text)
                    print(f"\n搜索结果:")
                    for i, item in enumerate(search_results[:3]):
                        title = item.get("title", "未知")
                        url = item.get("url", "未知")
                        print(f"\n  {i + 1}. {title}")
                        print(f"     URL: {url}")
                except json.JSONDecodeError:
                    print(f"\n响应内容（前500字符）:\n{result_text[:500]}...")

                print(f"\n完整长度: {len(result_text)} 字符")
                return True
            else:
                print("错误: 响应中没有 content 字段")
                return False
        else:
            print(f"错误: HTTP {response.status_code}")
            print(response.text[:500])
            return False

    except Exception as e:
        print(f"异常: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_web_fetch():
    """测试 web_fetch 工具"""
    print("\n" + "=" * 60)
    print("测试 web_fetch 工具")
    print("=" * 60)

    # 使用 GitHub README 作为测试 URL
    payload = {"arguments": {"url": "https://github.com/Saik0s/mcp-browser-use", "timeout": 30}}

    try:
        response = requests.post(f"{MCP_BASE_URL}/tools/web_fetch", headers={"Content-Type": "application/json"}, json=payload, timeout=60)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n响应类型: {result.get('meta', {}).get('contentType', 'unknown')}")

            content = result.get("content", [])
            if content:
                result_text = content[0].get("text", "无响应")
                print(f"\n响应内容（前500字符）:\n{result_text[:500]}...")
                print(f"\n完整长度: {len(result_text)} 字符")

                # 检查是否包含预期的内容
                if "mcp-browser-use" in result_text.lower():
                    print("\n✅ 内容验证通过: 包含 'mcp-browser-use'")
                    return True
                else:
                    print("\n⚠️  内容验证失败: 未找到预期的关键字")
                    return False
            else:
                print("错误: 响应中没有 content 字段")
                return False
        else:
            print(f"错误: HTTP {response.status_code}")
            print(response.text[:500])
            return False

    except Exception as e:
        print(f"异常: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("开始测试 MCP Web 工具...")
    print(f"MCP 服务地址: {MCP_BASE_URL}\n")

    # 先获取工具列表，确认 web_search 和 web_fetch 是否注册
    tools = list_tools()

    if "web_search" in tools and "web_fetch" in tools:
        print("\n✅ 两个 Web 工具均已注册，继续测试...\n")

        test1 = test_web_search()
        test2 = test_web_fetch()

        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        print(f"web_search: {'✅ 通过' if test1 else '❌ 失败'}")
        print(f"web_fetch:  {'✅ 通过' if test2 else '❌ 失败'}")

        if test1 and test2:
            print("\n所有测试通过 ✅")
            sys.exit(0)
        else:
            print("\n部分测试失败 ❌")
            sys.exit(1)
    else:
        print("\n❌ Web 工具未注册，无法测试")
        sys.exit(1)
