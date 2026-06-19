#!/usr/bin/env python3
"""测试 winserver MCP 服务的 web_search 和 web_fetch 工具"""

import sys

import requests

MCP_BASE_URL = "http://192.168.110.250:8383"


def test_web_search():
    """测试 web_search 工具"""
    print("=" * 60)
    print("测试 web_search 工具")
    print("=" * 60)

    payload = {"arguments": {"query": "Python asyncio", "max_results": 3, "lang": "zh-CN"}}

    try:
        response = requests.post(f"{MCP_BASE_URL}/tools/web_search", headers={"Content-Type": "application/json"}, json=payload, timeout=60)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n响应类型: {result.get('meta', {}).get('contentType', 'unknown')}")

            content = result.get("content", [])
            if content:
                result_text = content[0].get("text", "无响应")
                print(f"\n响应内容（前500字符）:\n{result_text[:500]}...")
                print(f"\n完整长度: {len(result_text)} 字符")
                return True
            else:
                print("错误: 响应中没有 content 字段")
                return False
        else:
            print(f"错误: HTTP {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"异常: {e}")
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
            print(response.text)
            return False

    except Exception as e:
        print(f"异常: {e}")
        return False


if __name__ == "__main__":
    print("开始测试 MCP Web 工具...")
    print(f"MCP 服务地址: {MCP_BASE_URL}\n")

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
