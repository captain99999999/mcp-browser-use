#!/usr/bin/env python3
# ruff: noqa: RUF001, RUF003
"""Run repeated web_search checks against the winserver MCP endpoint."""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

WIN_SERVER_URL = "http://192.168.110.250:8383/mcp"
CAPTCHA_INDICATORS = [
    "unusual traffic",
    "from your computer network",
    "I'm not a robot",
    "reCAPTCHA",
    "verify you're human",
    "automated access",
    "blocked",
    "security check",
]

# 10 个多样化查询（中英文混合，不同长度）
TEST_QUERIES = [
    "Python tutorial for beginners",
    "如何学习机器学习",
    "React useState hook example",
    "Docker container 基础教程",
    "VS Code 快捷键大全",
    "API design best practices",
    "Kubernetes YAML configuration",
    "数据库索引优化技术",
    "Git workflow examples",
    "Web security OWASP top 10",
]


def _extract_text_payload(response: Any) -> str:
    """Extract text from FastMCP tool response objects for inspection."""
    if hasattr(response, "content") and response.content:
        chunks: list[str] = []
        for item in response.content:
            if hasattr(item, "text") and item.text:
                chunks.append(str(item.text))
            else:
                chunks.append(str(item))
        return "\n".join(chunks)
    return str(response)


def _extract_result_count(raw_text: str) -> int | None:
    """Best-effort parse of result count from returned text payload."""
    text = raw_text.strip()
    if not text:
        return 0
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, list):
        return len(parsed)
    if isinstance(parsed, dict):
        for key in ("results", "items", "content"):
            value = parsed.get(key)
            if isinstance(value, list):
                return len(value)
    return None


async def run_single_test(client: Client, query: str, idx: int) -> dict[str, Any]:
    """Run one web_search call and return structured result info."""
    start = time.time()
    result = {
        "idx": idx,
        "query": query,
        "elapsed": 0,
        "success": False,
        "captcha_detected": False,
        "result_count": 0,
    }

    try:
        print(f"[{idx}/10] Query: {query}")
        response = await client.call_tool("web_search", {"query": query, "max_results": 5})

        elapsed = time.time() - start
        result["elapsed"] = round(elapsed, 2)

        content = _extract_text_payload(response)

        # 检测 CAPTCHA
        content_lower = content.lower()
        for indicator in CAPTCHA_INDICATORS:
            if indicator.lower() in content_lower:
                result["captcha_detected"] = True
                result["captcha_indicator"] = indicator
                break

        if not result["captcha_detected"]:
            parsed_count = _extract_result_count(content)
            if parsed_count is not None:
                result["result_count"] = parsed_count
            else:
                # Fallback for non-JSON but non-empty responses.
                result["result_count"] = -1

        result["success"] = not result["captcha_detected"] and "error" not in result

        # 打印状态
        if result["captcha_detected"]:
            print(f"  ❌ CAPTCHA TRIGGERED ({elapsed:.1f}s) - {result.get('captcha_indicator')}")
        else:
            count_label = "unknown" if result["result_count"] == -1 else result["result_count"]
            print(f"  ✅ Success ({elapsed:.1f}s) - {count_label} results")

    except Exception as e:
        elapsed = time.time() - start
        result["elapsed"] = round(elapsed, 2)
        print(f"  ⚠️ ERROR ({elapsed:.1f}s): {e}")
        result["error"] = str(e)

    return result


async def main() -> None:
    print("=" * 70)
    print("🧪 web_search 验证测试 - 10 次查询")
    print("=" * 70)
    print(f"服务端点: {WIN_SERVER_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 建立连接 - 必须使用 async with 上下文管理器
    print("🔌 连接 winserver MCP 服务...")
    transport = StreamableHttpTransport(url=WIN_SERVER_URL)
    client = Client(transport=transport)

    async with client:
        print("✅ 连接成功")
        print()

        # 逐个执行测试（间隔 5 秒）
        results = []
        for i, query in enumerate(TEST_QUERIES, 1):
            result = await run_single_test(client, query, i)
            results.append(result)

            # 间隔 5 秒（除了最后一次）
            if i < len(TEST_QUERIES):
                print("  ⏳ 等待 5 秒...")
                await asyncio.sleep(5)

        print()
        print("=" * 70)
        print("📊 测试结果汇总")
        print("=" * 70)

        # 统计
        total = len(results)
        success = sum(1 for r in results if r["success"])
        captcha = sum(1 for r in results if r["captcha_detected"])
        errors = sum(1 for r in results if "error" in r)
        elapsed_list = [r["elapsed"] for r in results if "elapsed" in r]

        avg_elapsed = sum(elapsed_list) / len(elapsed_list) if elapsed_list else 0
        success_rate = (success / total) * 100
        captcha_rate = (captcha / total) * 100

        print(f"✅ 成功: {success}/{total} ({success_rate:.1f}%)")
        print(f"🚫 CAPTCHA: {captcha}/{total} ({captcha_rate:.1f}%)")
        print(f"⚠️ 错误: {errors}/{total}")
        print(f"⏱️ 平均响应时间: {avg_elapsed:.1f}s")
        print()

        # CAPTCHA 详情
        if captcha > 0:
            print("🚫 CAPTCHA 触发详情:")
            for r in results:
                if r["captcha_detected"]:
                    print(f"   [{r['idx']}] {r['query']} - {r['elapsed']}s - {r['captcha_indicator']}")
            print()

        # 稳定性评估
        print("=" * 70)
        print("📈 稳定性评估")
        print("=" * 70)

        if success_rate >= 90:
            stability = "🟢 稳定可用"
            recommendation = "反检测措施有效，可以继续依赖浏览器抓取路径"
        elif success_rate >= 80:
            stability = "🟡 基本可用"
            recommendation = "成功率接近稳定阈值，建议观察后续数据"
        elif success_rate >= 60:
            stability = "🟠 需要关注"
            recommendation = "成功率偏低，建议增加测试样本或讨论替代方案"
        else:
            stability = "🔴 不稳定"
            recommendation = "CAPTCHA 触发过多，必须重新评估技术路线"

        print(f"评估: {stability}")
        print(f"建议: {recommendation}")
        print()

        # 保存原始数据
        output_file = Path(__file__).resolve().parent / "test_results.json"
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "test_time": datetime.now().isoformat(),
                    "server_url": WIN_SERVER_URL,
                    "results": results,
                    "summary": {
                        "total": total,
                        "success": success,
                        "captcha": captcha,
                        "errors": errors,
                        "success_rate": success_rate,
                        "captcha_rate": captcha_rate,
                        "avg_elapsed": avg_elapsed,
                    },
                    "stability": stability,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"💾 原始数据已保存到: {output_file}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
