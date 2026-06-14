import asyncio, sys, os, json
sys.path.insert(0, r'D:\browser-projects\use-browser\mcp-browser-use\src')
os.environ['MCP_LLM_PROVIDER'] = 'deepseek'
os.environ['MCP_LLM_MODEL_NAME'] = 'deepseek-chat'
os.environ['DEEPSEEK_API_KEY'] = 'sk-88c270b2fef24ef492f97133c763c44c'
os.environ['MCP_BROWSER_CDP_URL'] = 'http://127.0.0.1:9222'
os.environ['MCP_BROWSER_HEADLESS'] = 'false'

from fastmcp import Client
from mcp_server_browser_use.server import serve

async def main():
    server = serve()
    async with Client(server) as client:
        print('=== 测试 web_search: Python async ===')
        result = await client.call_tool('web_search', {
            'query': 'Python asyncio tutorial',
            'max_results': 5,
            'max_queries': 1
        })
        text = result.content[0].text if hasattr(result, 'content') else str(result)
        print(text[:1500])

asyncio.run(main())