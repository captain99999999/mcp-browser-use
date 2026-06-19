#!/usr/bin/env python3
"""检查 MCP 服务上注册的工具列表"""

import json

import requests

MCP_BASE_URL = "http://192.168.110.250:8383"


def list_tools():
    """获取 MCP 工具列表"""
    print("= 获取 MCP 工具列表 =")
    print(f"MCP 服务地址: {MCP_BASE_URL}\n")

    try:
        response = requests.get(f"{MCP_BASE_URL}/tools", timeout=10)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n根响应结构: {result.get('meta', {}).keys()}")

            # 提取工具列表
            content = result.get("content", [])
            if content:
                tool_data = content[0]

                # 打印工具列表
                tool_list_text = tool_data.get("text", "无工具列表")
                print("\n工具列表解析中...")
                print(f"工具数据类型: {type(tool_list_text)}")

                # 尝试解析 JSON
                try:
                    tools = json.loads(tool_list_text)
                    print(f"\n找到 {len(tools)} 个工具:\n")

                    for tool in tools:
                        name = tool.get("name", "未知")
                        description = tool.get("description", "无描述")[:60]
                        print(f"- {name}: {description}...")
                except json.JSONDecodeError as e:
                    print(f"JSON 解析失败: {e}")
                    print(f"原始内容(前500字符):\n{tool_list_text[:500]}")
            else:
                print("错误: 响应中没有 content 字段")
        else:
            print(f"错误: HTTP {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"异常: {e}")


if __name__ == "__main__":
    list_tools()
