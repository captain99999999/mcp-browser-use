"""Web search utilities using LLM-optimized queries."""

import json
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from browser_use.llm.base import BaseChatModel

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Single search result."""

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


# DUCKDUCKGO_API_URL kept for future reference; not currently used by the server.
