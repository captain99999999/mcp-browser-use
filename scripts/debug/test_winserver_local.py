import asyncio
import sys

sys.path.insert(0, "src")
from fastmcp import Client


async def test():
    async with Client("http://127.0.0.1:8383/mcp", timeout=30) as c:
        r = await c.call_tool("web_search", {"query": "test", "max_results": 2, "max_queries": 1})
        if r.content:
            print(r.content[0].text[:500])
        else:
            print("empty result")


asyncio.run(test())
