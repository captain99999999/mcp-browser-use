"""Web search utilities using LLM-optimized queries and multi-engine support."""

import asyncio
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import unquote

if TYPE_CHECKING:
    from browser_use.llm.base import BaseChatModel
    from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Single search result."""

    title: str
    url: str
    snippet: str


@dataclass
class SearchEngineConfig:
    """Configuration for a search engine.

    Attributes:
        name: Engine identifier (e.g., "google", "bing", "baidu")
        search_url_template: URL template with {query} and optional {language} placeholders
        rate_limit_delay: Minimum delay between requests in seconds
        result_parser: Function that takes (soup: BeautifulSoup, html: str) and returns list[SearchResult]
        language_param: Query parameter name for language (None if not supported)
    """

    name: str
    search_url_template: str
    rate_limit_delay: float = 2.0
    result_parser: Callable[["BeautifulSoup", str], list["SearchResult"]] | None = None
    language_param: str | None = None


def _parse_google_results(soup: "BeautifulSoup", _html: str) -> list["SearchResult"]:
    """Parse Google search results from HTML."""
    results: list[SearchResult] = []

    for h3 in soup.select("h3"):
        title = h3.get_text(strip=True)
        if not title:
            continue

        # Find URL: walk up parent chain for an <a> with href
        url = ""
        parent = h3.parent
        for _ in range(10):
            if parent is None:
                break
            link = parent.select_one("a[href]")
            if link:
                href = link.get("href", "")
                if "/url?q=" in href:
                    url = href.split("/url?q=")[-1].split("&")[0]
                elif href.startswith("http"):
                    url = href
                if url:
                    break
            parent = parent.parent

        # Find snippet: walk up for a div with enough text
        snippet = ""
        parent = h3.parent
        for _ in range(8):
            if parent is None:
                break
            for div in parent.select("div"):
                text = div.get_text(strip=True)
                if text and len(text) > 30 and text != title:
                    snippet = text[:500]
                    break
            if snippet:
                break
            parent = parent.parent

        if title and url:
            results.append(SearchResult(title=title[:200], url=unquote(url), snippet=snippet))

    return results


def _parse_bing_results(soup: "BeautifulSoup", _html: str) -> list["SearchResult"]:
    """Parse Bing search results from HTML."""
    results: list[SearchResult] = []

    for algo in soup.select("#b_results .b_algo"):
        # Title and URL from h2 > a
        link = algo.select_one("h2 a")
        if not link:
            continue
        title = link.get_text(strip=True)
        url = link.get("href", "")
        if not title or not url:
            continue

        # Snippet from caption paragraph
        snippet = ""
        caption = algo.select_one(".b_caption p")
        if caption:
            snippet = caption.get_text(strip=True)[:500]

        results.append(SearchResult(title=title[:200], url=url, snippet=snippet))

    return results


def _parse_baidu_results(soup: "BeautifulSoup", _html: str) -> list["SearchResult"]:
    """Parse Baidu search results from HTML.

    Baidu uses its own redirect link format (https://www.baidu.com/link?...).
    We extract the real URL from the redirect when possible, otherwise keep the redirect URL.
    """
    results: list[SearchResult] = []

    for result_div in soup.select(".result, .result-op"):
        # Title: .result h3 a or .c-title a
        title_link = result_div.select_one("h3 a") or result_div.select_one(".c-title a")
        if not title_link:
            continue
        title = title_link.get_text(strip=True)
        url = title_link.get("href", "")
        if not title:
            continue

        # Baidu uses redirect URLs - try to extract real URL from mu attribute
        # or keep the redirect URL as-is (it works for navigation)
        mu = title_link.get("mu")
        if mu and mu.startswith("http"):
            url = mu

        # Snippet: .c-abstract or .result .c-span-last span
        snippet = ""
        abstract = result_div.select_one(".c-abstract")
        if abstract:
            snippet = abstract.get_text(strip=True)[:500]
        else:
            span_last = result_div.select_one(".c-span-last span")
            if span_last:
                snippet = span_last.get_text(strip=True)[:500]

        if title and url:
            results.append(SearchResult(title=title[:200], url=url, snippet=snippet))

    return results


# Search engine registry
SEARCH_ENGINES: dict[str, SearchEngineConfig] = {
    "google": SearchEngineConfig(
        name="google",
        search_url_template="https://www.google.com/search?q={query}&hl={language}",
        rate_limit_delay=2.0,
        result_parser=_parse_google_results,
        language_param="hl",
    ),
    "bing": SearchEngineConfig(
        name="bing",
        search_url_template="https://www.bing.com/search?q={query}&setlang={language}",
        rate_limit_delay=1.5,
        result_parser=_parse_bing_results,
        language_param="setlang",
    ),
    "baidu": SearchEngineConfig(
        name="baidu",
        search_url_template="https://www.baidu.com/s?wd={query}",
        rate_limit_delay=2.0,
        result_parser=_parse_baidu_results,
        language_param=None,
    ),
}


def get_search_engine_config(engine: str) -> SearchEngineConfig | None:
    """Get the configuration for a search engine.

    Args:
        engine: Engine name (e.g., "google", "bing", "baidu")

    Returns:
        SearchEngineConfig or None if engine is not registered.
    """
    return SEARCH_ENGINES.get(engine.lower())


async def generate_search_queries(topic: str, llm: "BaseChatModel", max_queries: int = 3) -> list[str]:
    """Generate optimized search queries using LLM with retry.

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

    # Retry once on LLM failure
    for attempt in range(2):
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
            logger.warning(f"Failed to parse JSON from LLM response (attempt {attempt + 1}): {e}")
            if attempt == 0:
                await asyncio.sleep(1.0)  # Brief wait before retry
                continue
            # Final attempt: extract from text
            try:
                lines = [line.strip().strip("-").strip("*").strip('"') for line in content.split("\n") if line.strip()]
                if lines:
                    return lines[:max_queries]
            except Exception:
                pass
            return [topic]

        except Exception as e:
            logger.error(f"Error generating search queries (attempt {attempt + 1}): {e}")
            if attempt == 0:
                await asyncio.sleep(1.0)
                continue
            return [topic]

    return [topic]  # Should not reach here


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
