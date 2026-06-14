"""Web search utilities using LLM-optimized queries and DuckDuckGo API."""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from browser_use.llm.base import BaseChatModel

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Single search result from DuckDuckGo API."""

    title: str
    url: str
    snippet: str


# DuckDuckGo Instant Answer API - no API key required
DUCKDUCKGO_API_URL = "https://api.duckduckgo.com/"


async def generate_search_queries(topic: str, llm: "BaseChatModel", max_queries: int = 3) -> list[str]:
    """Generate optimized search queries using LLM.

    Args:
        topic: The search topic or question
        llm: LLM instance for query generation
        max_queries: Maximum number of queries to generate

    Returns:
        List of optimized search query strings
    """
    from browser_use.llm.messages import SystemMessage, UserMessage

    system_prompt = """You are a search query optimizer. Your task is to generate effective search queries that will return comprehensive and relevant results.

Rules:
- Generate specific, focused queries (not too broad or too narrow)
- Cover different aspects of the topic (definitions, examples, applications, etc.)
- Each query should be 3-8 words
- Return ONLY a JSON array of query strings, nothing else

Example:
Input: "quantum computing applications"
Output: ["quantum computing applications", "quantum algorithms uses", "quantum machine learning"]"""

    user_prompt = f"""Generate {max_queries} search queries for: {topic}

Return ONLY a JSON array of {max_queries} search query strings."""

    messages = [
        SystemMessage(content=system_prompt),
        UserMessage(content=user_prompt),
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.completion

        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        # Parse JSON
        queries = json.loads(content)
        if isinstance(queries, list):
            return queries[:max_queries]

        # Fallback: try to extract from text
        lines = re.findall(r'"([^"]+)"', content)
        if lines:
            return lines[:max_queries]

        # Final fallback: return original topic
        logger.warning(f"Failed to parse LLM response, using fallback: {content[:100]}")
        return [topic]

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from LLM response: {e}, using fallback")
        # Try to extract queries from text
        lines = [line.strip().strip("-").strip("*").strip('"') for line in content.split("\n") if line.strip()]
        if lines:
            return lines[:max_queries]
        return [topic]

    except Exception as e:
        logger.error(f"Error generating search queries: {e}")
        return [topic]


async def search_duckduckgo(query: str, max_results: int = 10, timeout: float = 10.0, proxy: str | None = None) -> list[SearchResult]:
    """Search using DuckDuckGo Instant Answer API.

    Args:
        query: Search query string
        max_results: Maximum number of results to return
        timeout: Request timeout in seconds
        proxy: Optional proxy URL (e.g., http://127.0.0.1:7897)

    Returns:
        List of SearchResult objects
    """
    import os

    proxy_url = proxy or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("MCP_PROXY")

    try:
        async with httpx.AsyncClient(timeout=timeout, proxy=proxy_url, follow_redirects=True) as client:
            response = await client.get(
                DUCKDUCKGO_API_URL,
                params={"q": query, "format": "json"},
            )
            # DuckDuckGo returns 202 for some queries (still contains valid data)
            if response.status_code not in (200, 202):
                response.raise_for_status()
            data = response.json()

            # Parse DuckDuckGo response format
            results = []

            if "RelatedTopics" in data:
                for topic in data["RelatedTopics"][:max_results]:
                    first_url = topic.get("FirstURL")
                    text = topic.get("Text")
                    if first_url and text:
                        results.append(
                            SearchResult(
                                title=text.split(" - ")[0] if " - " in text else text,
                                url=first_url,
                                snippet=topic.get("Result", "") or text,
                            )
                        )

            # Fallback to AbstractText if available
            if not results and "AbstractText" in data:
                abstract = data.get("AbstractText", "")
                abstract_url = data.get("AbstractURL", "")
                if abstract and abstract_url:
                    results.append(SearchResult(title="DuckDuckGo Result", url=abstract_url, snippet=abstract))

            return results

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error searching DuckDuckGo: {e}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Network error searching DuckDuckGo: {e}")
        raise
    except Exception as e:
        logger.error(f"Error searching DuckDuckGo: {e}")
        raise


def deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    """Remove duplicate search results by URL.

    Args:
        results: List of search results

    Returns:
        Deduplicated list of SearchResult objects
    """
    seen_urls = set()
    unique_results = []

    for result in results:
        if result.url not in seen_urls:
            seen_urls.add(result.url)
            unique_results.append(result)

    return unique_results


def as_dict(result: SearchResult) -> dict:
    """Convert SearchResult to dictionary.

    Args:
        result: SearchResult object

    Returns:
        Dictionary representation
    """
    return {
        "title": result.title,
        "url": result.url,
        "snippet": result.snippet,
    }