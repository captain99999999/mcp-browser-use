"""End-to-end integration tests for web_search and web_fetch MCP tools.

These tests require:
- A valid LLM API key (DEEPSEEK_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, etc.)
- A running Chrome instance reachable via CDP (default: http://127.0.0.1:9222)
- Network access to Google

Mark: @pytest.mark.e2e
"""

import os
from collections.abc import AsyncGenerator

import pytest
from fastmcp import Client

# Skip entire module if no API key is configured
API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not API_KEY, reason="No LLM API key configured for e2e tests"),
]


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def web_client(monkeypatch) -> AsyncGenerator[Client, None]:
    """Create an MCP client for web tools e2e tests.

    Defaults:
    - LLM: deepseek / deepseek-chat (fast + cheap for query optimization)
    - CDP: http://127.0.0.1:9222 (relies on browser-pool running locally)
    - Headless: false (Windows CDP requires desktop session)
    """
    # Configure environment for the test
    if os.environ.get("DEEPSEEK_API_KEY"):
        monkeypatch.setenv("MCP_LLM_PROVIDER", "deepseek")
        monkeypatch.setenv("MCP_LLM_MODEL_NAME", "deepseek-chat")
    elif os.environ.get("GEMINI_API_KEY"):
        monkeypatch.setenv("MCP_LLM_PROVIDER", "google")
        monkeypatch.setenv("MCP_LLM_MODEL_NAME", "gemini-2.0-flash")
    elif os.environ.get("OPENAI_API_KEY"):
        monkeypatch.setenv("MCP_LLM_PROVIDER", "openai")
        monkeypatch.setenv("MCP_LLM_MODEL_NAME", "gpt-4o-mini")
    elif os.environ.get("ANTHROPIC_API_KEY"):
        monkeypatch.setenv("MCP_LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("MCP_LLM_MODEL_NAME", "claude-3-haiku-20240307")

    monkeypatch.setenv("MCP_BROWSER_CDP_URL", "http://127.0.0.1:9222")
    monkeypatch.setenv("MCP_BROWSER_HEADLESS", "false")

    # Reload config and server modules to pick up new env vars
    import importlib

    import mcp_server_browser_use.config
    import mcp_server_browser_use.server

    importlib.reload(mcp_server_browser_use.config)
    importlib.reload(mcp_server_browser_use.server)

    from mcp_server_browser_use.server import serve

    app = serve()
    async with Client(app) as client:
        yield client


def _extract_text(result) -> str:
    """Extract text from a FastMCP tool result."""
    if hasattr(result, "content") and result.content:
        first = result.content[0]
        if hasattr(first, "text"):
            return first.text
        return str(first)
    if hasattr(result, "data"):
        return str(result.data)
    return str(result)


@pytest.mark.anyio
@pytest.mark.slow
async def test_web_search_chinese(web_client: Client):
    """web_search should return results for a Chinese query."""
    result = await web_client.call_tool(
        "web_search",
        {
            "query": "万科房地产公司2024经营状况",
            "max_results": 5,
            "max_queries": 1,
        },
    )
    text = _extract_text(result)
    assert text, "web_search returned empty content"
    # Should contain at least one valid-looking URL
    assert "http" in text, f"Expected URLs in result, got: {text[:300]}"


@pytest.mark.anyio
@pytest.mark.slow
async def test_web_search_english(web_client: Client):
    """web_search should return results for an English query."""
    result = await web_client.call_tool(
        "web_search",
        {
            "query": "Python asyncio tutorial",
            "max_results": 5,
            "max_queries": 1,
        },
    )
    text = _extract_text(result)
    assert text
    assert "http" in text, f"Expected URLs in result, got: {text[:300]}"


@pytest.mark.anyio
@pytest.mark.slow
async def test_web_fetch_text(web_client: Client):
    """web_fetch should retrieve text content from a URL."""
    result = await web_client.call_tool(
        "web_fetch",
        {
            "url": "https://realpython.com/async-io-python/",
            "output_format": "text",
        },
    )
    text = _extract_text(result)
    assert text, "web_fetch returned empty content"
    # Real Python async tutorial is long; expect a non-trivial response
    assert len(text) > 1000, f"Expected >1000 chars, got {len(text)}"


@pytest.mark.anyio
@pytest.mark.slow
async def test_list_tools_includes_web_tools(web_client: Client):
    """The MCP server should expose web_search and web_fetch as registered tools."""
    tools = await web_client.list_tools()
    names = {t.name for t in tools}
    assert "web_search" in names, f"web_search not registered. Tools: {names}"
    assert "web_fetch" in names, f"web_fetch not registered. Tools: {names}"
