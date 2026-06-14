#!/usr/bin/env python3
"""
在 winserver 上添加 web_search 和 web_fetch 工具
这个脚本会修改 server.py 文件，添加两个新的 MCP 工具。
"""

import os
import sys
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path(r"C:\Users\Administrator\src\mcp_server_browser_use")
SERVER_FILE = PROJECT_ROOT / "server.py"

# 搜索模块路径（需要创建）
SEARCH_FILE = PROJECT_ROOT / "search.py"

# 搜索工具代码
SEARCH_IMPORT = """from mcp_server_browser_use.search import (
    generate_search_queries,
    search_duckduckgo,
    deduplicate_results,
    SearchResult,
)
"""

# web_search 工具代码
WEB_SEARCH_TOOL = '''
    # --- Web Tools ---

    @server.tool(task=TaskConfig(mode="optional"))
    async def web_search(
        query: str,
        max_results: int = 10,
        max_queries: int = 3,
        ctx: Context = CurrentContext(),
        progress: Progress = Progress(),
    ) -> str:
        """
        Search the web using AI-optimized queries.

        Executes as a background task if client requests it, otherwise synchronous.
        Progress updates are streamed via the MCP task protocol.

        Args:
            query: Search query or question
            max_results: Maximum number of results to return (default 10)
            max_queries: Number of search queries to generate (default 3)

        Returns:
            JSON array of search results with title, url, and snippet
        """
        import json

        # --- Task Tracking Setup ---
        task_id = str(uuid.uuid4())
        task_store = get_task_store()
        task_record = TaskRecord(
            task_id=task_id,
            tool_name="web_search",
            status=TaskStatus.PENDING,
            input_params={"query": query, "max_results": max_results, "max_queries": max_queries},
        )
        await task_store.create_task(task_record)
        bind_task_context(task_id, "web_search")
        task_logger = get_task_logger()

        await ctx.info(f"Starting web search: {query}")
        logger.info(f"Starting web search: {query[:100]}...")
        task_logger.info("task_created", query_preview=query[:100])

        try:
            llm, profile = _get_llm_and_profile()
        except LLMProviderError as e:
            logger.error(f"LLM initialization failed: {e}")
            await task_store.update_status(task_id, TaskStatus.FAILED, error=str(e))
            clear_task_context()
            return f"Error: {e}"

        # Mark task as running
        await task_store.update_status(task_id, TaskStatus.RUNNING)
        await task_store.update_progress(task_id, 0, 3, "Initializing...")
        task_logger.info("task_running")

        # Step 1: Generate search queries using LLM
        await progress.set_total(3)
        await ctx.info("Generating optimized search queries...")
        logger.info(f"Generating {max_queries} search queries for: {query}")

        try:
            search_queries = await generate_search_queries(query, llm, max_queries)
        except Exception as e:
            logger.error(f"Failed to generate search queries: {e}")
            search_queries = [query]  # Fallback to original query

        await progress.increment()
        await ctx.info(f"Generated {len(search_queries)} search queries")

        # Step 2: Execute searches
        await task_store.update_progress(task_id, 1, 3, "Searching...")
        all_results = []

        for i, search_query in enumerate(search_queries, 1):
            await ctx.info(f"Searching ({i}/{len(search_queries)}): {search_query[:50]}...")
            logger.info(f"Executing search {i}/{len(search_queries)}: {search_query}")

            try:
                results = await search_duckduckgo(search_query, max_results)
                all_results.extend(results)
                logger.info(f"Search '{search_query[:30]}...' returned {len(results)} results")
            except Exception as e:
                logger.error(f"Search failed for query '{search_query[:30]}...': {e}")

        await progress.increment()

        # Step 3: Deduplicate and limit results
        unique_results = deduplicate_results(all_results)[:max_results]
        await task_store.update_progress(task_id, 2, 3, "Processing results...")

        result_json = json.dumps([{"title": r.title, "url": r.url, "snippet": r.snippet} for r in unique_results], indent=2)

        await ctx.info(f"Search completed: {len(unique_results)} results")
        logger.info(f"Web search completed: {len(unique_results)} results found")

        # Mark task as completed
        await task_store.update_status(task_id, TaskStatus.COMPLETED, result=result_json[:500])
        task_logger.info("task_completed", result_count=len(unique_results))
        clear_task_context()
        return result_json

    except asyncio.CancelledError:
        await task_store.update_status(task_id, TaskStatus.CANCELLED, error="Cancelled by user")
        task_logger.info("task_cancelled")
        clear_task_context()
        raise
    except Exception as e:
        await task_store.update_status(task_id, TaskStatus.FAILED, error=str(e))
        task_logger.error("task_failed", error=str(e))
        clear_task_context()
        logger.error(f"Web search failed: {e}")
        raise
'''

# web_fetch 工具代码
WEB_FETCH_TOOL = '''
    @server.tool(task=TaskConfig(mode="optional"))
    async def web_fetch(
        url: str,
        output_format: str = "html",
        wait_for_selector: str | None = None,
        ctx: Context = CurrentContext(),
        progress: Progress = Progress(),
    ) -> str:
        """
        Fetch web page content with JavaScript rendering support.

        Executes as a background task if client requests it, otherwise synchronous.
        Progress updates are streamed via the MCP task protocol.

        Args:
            url: The URL to fetch
            output_format: Output format (html, text, or screenshot) (default: html)
            wait_for_selector: Optional CSS selector to wait for (for dynamic content)

        Returns:
            Page content as HTML, plain text, or base64-encoded screenshot
        """
        import base64

        # --- Task Tracking Setup ---
        task_id = str(uuid.uuid4())
        task_store = get_task_store()
        task_record = TaskRecord(
            task_id=task_id,
            tool_name="web_fetch",
            status=TaskStatus.PENDING,
            input_params={"url": url, "output_format": output_format, "wait_for_selector": wait_for_selector},
        )
        await task_store.create_task(task_record)
        bind_task_context(task_id, "web_fetch")
        task_logger = get_task_logger()

        await ctx.info(f"Fetching: {url}")
        logger.info(f"Starting web fetch: {url[:100]}...")
        task_logger.info("task_created", url=url[:100])

        try:
            llm, profile = _get_llm_and_profile()
        except LLMProviderError as e:
            logger.error(f"LLM initialization failed: {e}")
            await task_store.update_status(task_id, TaskStatus.FAILED, error=str(e))
            clear_task_context()
            return f"Error: {e}"

        # Mark task as running
        await task_store.update_status(task_id, TaskStatus.RUNNING)
        await task_store.update_progress(task_id, 0, 2, "Initializing browser...")
        task_logger.info("task_running")

        # Validate URL
        if not url.startswith(("http://", "https://")):
            error = f"Invalid URL: {url}"
            logger.error(error)
            await task_store.update_status(task_id, TaskStatus.FAILED, error=error)
            clear_task_context()
            return f"Error: {error}"

        # Validate output format
        valid_formats = ["html", "text", "screenshot"]
        if output_format not in valid_formats:
            error = f"Invalid output_format: {output_format}. Valid formats: {', '.join(valid_formats)}"
            logger.error(error)
            await task_store.update_status(task_id, TaskStatus.FAILED, error=error)
            clear_task_context()
            return f"Error: {error}"

        # Start browser session
        from browser_use.browser.session import BrowserSession

        await task_store.update_progress(task_id, 1, 2, "Loading page...")

        browser_session = BrowserSession(browser_profile=profile)
        await browser_session.start()

        try:
            # Navigate to page
            await ctx.info(f"Navigating to: {url[:80]}...")
            await browser_session.goto(url)

            # Wait for selector if specified
            if wait_for_selector:
                await ctx.info(f"Waiting for selector: {wait_for_selector}")
                try:
                    await browser_session.wait_for_selector(wait_for_selector, timeout=10000)
                    logger.info(f"Selector found: {wait_for_selector}")
                except Exception as e:
                    logger.warning(f"Wait for selector failed: {e}")
                    await ctx.info(f"Warning: Selector not found, proceeding: {str(e)[:50]}")

            # Extract content based on format
            await ctx.info(f"Extracting content as {output_format}...")
            logger.info(f"Extracting content in {output_format} format")

            if output_format == "html":
                content = await browser_session.page.content()
            elif output_format == "text":
                content = await browser_session.page.evaluate("() => document.body.innerText")
            elif output_format == "screenshot":
                screenshot_bytes = await browser_session.page.screenshot(full_page=False)
                content = f"data:image/png;base64,{base64.b64encode(screenshot_bytes).decode()}"
            else:
                # This should not happen due to validation above
                raise ValueError(f"Invalid output_format: {output_format}")

            # Truncate content if too long
            MAX_CONTENT_SIZE = 100000
            if len(content) > MAX_CONTENT_SIZE:
                truncated_content = content[:MAX_CONTENT_SIZE]
                truncated_content += "\\n\\n... (content truncated due to size limit)"
                await ctx.info(f"Content truncated from {len(content)} to {MAX_CONTENT_SIZE} characters")
                logger.info(f"Content truncated from {len(content)} to {MAX_CONTENT_SIZE} characters")
                content = truncated_content

            await progress.increment()
            await ctx.info("Fetch completed")
            logger.info(f"Web fetch completed: {len(content)} characters ({output_format})")

            # Mark task as completed
            await task_store.update_status(task_id, TaskStatus.COMPLETED, result=content[:500])
            task_logger.info("task_completed", content_length=len(content), format=output_format)
            clear_task_context()
            return content

        finally:
            await browser_session.stop()

    except asyncio.CancelledError:
        await task_store.update_status(task_id, TaskStatus.CANCELLED, error="Cancelled by user")
        task_logger.info("task_cancelled")
        clear_task_context()
        raise
    except Exception as e:
        await task_store.update_status(task_id, TaskStatus.FAILED, error=str(e))
        task_logger.error("task_failed", error=str(e))
        clear_task_context()
        logger.error(f"Web fetch failed: {e}")
        raise
'''

def modify_server_file():
    """修改 server.py 文件，添加搜索工具的导入和新工具"""

    if not SERVER_FILE.exists():
        print(f"Error: Server file not found at {SERVER_FILE}")
        return False

    print(f"Modifying {SERVER_FILE}...")

    # 读取文件内容
    with open(SERVER_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 在导入部分添加 search 模块导入
    # 找到技能导入部分并添加
    skills_import_pattern = r'(from \.skills import.*?)$'
    import_match = re.search(skills_import_pattern, content, re.MULTILINE)

    if not import_match:
        print("Error: Could not find skills import statement")
        return False

    skills_line = import_match.group(0)
    insert_pos = import_match.end()

    new_import_line = skills_line + "\\n\\n" + SEARCH_IMPORT + "\\n"

    # 替换：添加搜索导入
    content = content[:insert_pos] + new_import_line + content[insert_pos:]

    # 2. 添加 web_search 和 web_fetch 工具
    # 找到 "# --- Observability Tools ---" 的位置
    obs_tools_pattern = r'# --- Observability Tools ---'
    obs_match = re.search(obs_tools_pattern, content)

    if not obs_match:
        print("Error: Could not find '# --- Observability Tools ---'")
        return False

    obs_pos = obs_match.start()
    content = content[:obs_pos] + WEB_SEARCH_TOOL + "\\n\\n" + WEB_FETCH_TOOL + "\\n\\n" + content[obs_pos:]

    # 写回文件
    with open(SERVER_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ Successfully modified server.py")
    print(f"✓ Added web_search tool")
    print(f"✓ Added web_fetch tool")
    print(f"✓ Added search module import")

    return True


if __name__ == "__main__":
    print("Adding web_search and web_fetch tools to winserver deployment...")

    # 1. 确保 search.py 文件存在
    if not SEARCH_FILE.exists():
        print(f"⚠️  Warning: search.py not found at {SEARCH_FILE}")
        print("   Please ensure the file was uploaded successfully.")

    # 2. 修改 server.py 文件
    if modify_server_file():
        print("\\n✓ Deployment update complete!")
        print("\\n⚠️  Note: You may need to:")
        print("   1. Stop the MCP server on winserver")
        print("   2. Install/update dependencies (uv sync)")
        print("   3. Restart the MCP server")
    else:
        print("\\n❌ Deployment update failed")
        sys.exit(1)