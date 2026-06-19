---
applyTo: "**/*.py"
---

# Python coding standards for mcp-browser-use

Follow these rules when editing any `.py` file in this repository.

## Required pre-commit checks

Always run **all** of these before committing — pre-commit hooks enforce them:

```bash
uv run ruff format .       # format (mandatory)
uv run ruff check .        # lint (mandatory)
uv run pyright             # type check (mandatory)
uv run pytest -m "not e2e" # unit + integration tests
```

## Style

- **Python 3.11+** with full type annotations
- **Line length: 150 characters** (per `pyproject.toml`)
- Use `async` / `await` for all I/O operations
- **Type hints required** for all functions; never use `any`
- **Docstrings required** for public APIs

## MCP tool pattern

Every new tool needs both a decorator AND a `TaskConfig` for background-task support:

```python
@server.tool(task=TaskConfig(mode="optional"))
async def my_tool(
    param: str,
    ctx: Context = CurrentContext(),
    progress: Progress = Progress(),
) -> str:
    """Tool description shown to LLM clients."""
    # Task tracking setup
    task_id = str(uuid.uuid4())
    task_store = get_task_store()
    task_record = TaskRecord(
        task_id=task_id,
        tool_name="my_tool",
        status=TaskStatus.PENDING,
        input_params={"param": param},
    )
    await task_store.create_task(task_record)
    bind_task_context(task_id, "my_tool")
    task_logger = get_task_logger()

    try:
        # ... actual work ...
        await task_store.update_status(task_id, TaskStatus.COMPLETED, result=result[:500])
        return result
    except Exception as e:
        await task_store.update_status(task_id, TaskStatus.FAILED, error=str(e))
        raise
    finally:
        clear_task_context()
```

See `web_search` in `src/mcp_server_browser_use/server.py` for the canonical example.

## Configuration

```python
from mcp_server_browser_use.config import settings
settings.browser.headless    # access config values
```

## Testing

- **NEVER** add `@pytest.mark.asyncio` — it's configured globally in `pyproject.toml`
- Imports go at the top of the file, not in test bodies
- For e2e tests that need a real LLM API key, use `@pytest.mark.skipif(not API_KEY, reason=...)` to skip cleanly when keys are missing
- Reference test file: `tests/integration_tests/test_web_tools.py`

## What NOT to do

- Don't hardcode API keys or secrets in source — use environment variables
- Don't push to upstream `Saik0s/mcp-browser-use`
- Don't commit `.env` files
- Don't write test files at the repo root (blocked by `.gitignore`); use `tests/` or `tests/integration_tests/`
