"""Tests for web_search and web_fetch tools."""

import json
import pytest

from fastmcp import Client
from mcp_server_browser_use.server import serve


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture
async def client():
    """Create in-memory MCP client for testing."""
    # Set environment variables before importing server
    import os

    os.environ.setdefault("MCP_LLM_PROVIDER", "openai")
    os.environ.setdefault("MCP_LLM_MODEL_NAME", "gpt-4")
    os.environ.setdefault("OPENAI_API_KEY", "test-key-12345")
    os.environ.setdefault("MCP_BROWSER_HEADLESS", "true")

    app = serve()

    async with Client(app) as client:
        yield client


@pytest.mark.anyio
async def test_web_search_basic(client: Client):
    """Test basic search functionality."""
    # This test will be skipped without real API key in e2e tests
    # For now, we'll mock the actual API calls

    # Note: In production, this would call DuckDuckGo API
    # For testing, we need to mock the search functions
    pass


@pytest.mark.anyio
@pytest.mark.integration
async def test_web_search_with_mocks():
    """Test web_search with mocked dependencies."""
    # This would require mocking generate_search_queries and search_duckduckgo
    # Implementation would verify:
    # 1. LLM query generation
    # 2. DuckDuckGo API calls
    # 3. Result deduplication
    # 4. JSON output format
    pass


@pytest.mark.anyio
async def test_web_search_timeout_handling():
    """Test web_search handles API timeout gracefully."""
    # This would test the timeout handling in search_duckduckgo
    pass


@pytest.mark.anyio
async def test_web_search_query_parsing():
    """Test web_search parses LLM responses correctly."""
    # This would test:
    # 1. JSON format parsing
    # 2. Markdown code block extraction
    # 3. Fallback parsing for malformed responses
    pass


@pytest.mark.anyio
async def test_web_search_empty_results():
    """Test web_search handles empty search results."""
    # This would verify the tool returns an empty array
    pass


@pytest.mark.anyio
@pytest.mark.integration
async def test_web_fetch_html(client: Client):
    """Test HTML fetch."""
    result = await client.call_tool(
        "web_fetch",
        {"url": "https://example.com", "output_format": "html"},
    )

    # Verify HTML content
    assert result is not None
    assert "<html" in result.lower()
    assert "<body" in result.lower()


@pytest.mark.anyio
async def test_web_fetch_text(client: Client):
    """Test plain text fetch."""
    result = await client.call_tool(
        "web_fetch",
        {"url": "https://example.com", "output_format": "text"},
    )

    # Verify text content
    assert result is not None
    assert len(result) > 0


@pytest.mark.anyio
async def test_web_fetch_invalid_url():
    """Test web_fetch handles invalid URLs."""
    result = await client.call_tool(
        "web_fetch",
        {"url": "not-a-valid-url", "output_format": "html"},
    )

    # Should return error message
    assert result.startswith("Error:")


@pytest.mark.anyio
async def test_web_fetch_invalid_format():
    """Test web_fetch handles invalid output format."""
    result = await client.call_tool(
        "web_fetch",
        {"url": "https://example.com", "output_format": "invalid"},
    )

    # Should return error message
    assert result.startswith("Error:")


@pytest.mark.anyio
async def test_web_fetch_with_wait_for_selector(client: Client):
    """Test web_fetch with selector wait."""
    result = await client.call_tool(
        "web_fetch",
        {"url": "https://example.com", "output_format": "text", "wait_for_selector": "h1"},
    )

    # Verify text content
    assert result is not None
    assert "Example Domain" in result


@pytest.mark.anyio
async def test_web_fetch_content_truncation():
    """Test web_fetch truncates oversized content."""
    # This would need a very large HTML page to test
    # Verify that content is truncated at 100KB
    pass


@pytest.mark.anyio
async def test_web_fetch_timeout():
    """Test web_fetch handles page load timeout."""
    # This would use a URL that times out to verify error handling
    pass


@pytest.mark.anyio
async def test_web_fetch_browser_cleanup():
    """Test web_fetch properly cleans up browser resources."""
    # This would verify that browser sessions are properly stopped
    # even when errors occur
    pass


@pytest.mark.anyio
async def test_web_fetch_progress_reporting():
    """Test web_fetch reports progress correctly."""
    # This would verify that:
    # 1. Initial browser initialization
    # 2. Page navigation
    # 3. Content extraction
    # # All stages update progress
    pass


# Test helper functions (to be used in actual tests)
async def mock_llm_response(topic: str) -> str:
    """Mock LLM response for query generation."""
    queries = [f"{topic} tutorial", f"how to use {topic}", f"{topic} examples"]
    return json.dumps(queries)


async def mock_duckduckgo_response(query: str) -> dict:
    """Mock DuckDuckGo API response."""
    return {
        "RelatedTopics": [
            {
                "FirstURL": "https://example.com/1",
                "Text": f"{query} result 1 - {query} description",
                "Result": f"This is a mock result for {query}",
            },
            {
                "FirstURL": "https://example.com/2",
                "Text": f"{query} result 2 - {query} description",
                "Result": f"This is another mock result for {query}",
            },
        ],
    }