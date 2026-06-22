# mcp-browser-use — Copilot cloud agent guide

> **Target reader**: GitHub Copilot cloud agent working on this repository for the first time.
> Keep this file under 2 pages. Focus on what the agent must know to make a safe, buildable change.

## What this repository is

This is an **internal fork** of [Saik0s/mcp-browser-use](https://github.com/Saik0s/mcp-browser-use) — an MCP server that wraps [browser-use](https://github.com/browser-use/browser-use) for AI-driven browser automation. The fork adds:

- **Handover Lock** — task pause/resume for multi-operator collaboration (`task_pause`, `task_resume` tools)
- **`web_search` / `web_fetch` tools** — Google-based search and JS-rendered page fetch

The fork is hosted at `github.com/captain99999999/mcp-browser-use`. **Do not push to the upstream `Saik0s` repository.**

## Repository topology

| Role | Location |
|---|---|
| Upstream (read-only) | `github.com/Saik0s/mcp-browser-use` |
| This fork (push target) | `github.com/captain99999999/mcp-browser-use` |
| Local dev | `e:\项目代码\mcp-browser-use` |
| Production deployment | `winserver` (192.168.110.250), `D:\browser-projects\mcp-browser-use\` |

**Branch**: All development happens on `fev`. `main` is read-only and tracks upstream.

## High-level project layout

```
src/
├── mcp_server_browser_use/        # server, tools, observability, skills, research
│   ├── server.py                  # FastMCP server + all @server.tool() definitions
│   ├── cli.py                     # Typer CLI
│   ├── config.py                  # Pydantic settings (LLM, browser, server, skills, research)
│   ├── providers.py               # 12 LLM providers
│   ├── observability/             # SQLite task tracking
│   ├── skills/                    # machine-learned browser skills
│   └── research/                  # deep research workflow
└── mcp_server_browser_utils/      # fork-specific: Google HTML parser + query generator
tests/                             # pytest (unit + integration_tests/)
scripts/                           # operational scripts
├── debug/                         # ad-hoc diagnostic scripts (never in project root)
docs/                              # design notes
AGENTS.md                          # full dev guidelines
docs/FASTMCP_PREVENTION_STRATEGIES.md   # FastMCP-specific gotchas
```

## Build & validate

Run **all** of these in order before committing:

```bash
uv sync                                    # install deps (use uv, never pip)
uv run ruff format .                       # format
uv run ruff check .                        # lint
uv run pyright                             # type check
uv run pytest -m "not e2e"                 # unit + integration tests (skip e2e without API key)
```

E2E tests (`tests/integration_tests/test_web_tools.py` and similar) require:
- `DEEPSEEK_API_KEY` (or other LLM key) in env
- A live Chrome at `http://127.0.0.1:9222` (browser-pool)
- `PYTHONPATH=D:\browser-projects\mcp-browser-use\src` when using a foreign venv

## Commit & push rules

- **Never push to upstream.** Only `origin` (the `captain99999999` fork) accepts pushes.
- Branch: `fev`. Default remote branch: `fev`.
- Use conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`.
- Do **not** commit secrets. `DEEPSEEK_API_KEY` lives in `D:\browser-projects\use-browser\.env` on winserver, not in the repo.
- Do **not** modify `winserver` deployment files directly. They get synced from this repo.

## Common pitfalls

- **Tool definition pattern**: every new MCP tool needs both `@server.tool(...)` decorator AND a `TaskConfig(mode="optional")` if it should run as a background task. See `web_search` in `server.py` for the canonical example.
- **Test location**: all tests must go in `tests/` or `tests/integration_tests/`. Ad-hoc debug scripts go in `scripts/debug/`, never in the project root.
- **README code blocks**: must declare a language tag (e.g., ```text for ASCII diagrams).

## Detailed references (read on demand)

- Fork-specific workflow, deployment, upstream sync → [copilot-instructions.md](copilot-instructions.md)
- Coding standards, test patterns, CI fix order → [AGENTS.md](../AGENTS.md)
- User-facing docs → [README.md](../README.md)
- FastMCP gotchas → [docs/FASTMCP_PREVENTION_STRATEGIES.md](../docs/FASTMCP_PREVENTION_STRATEGIES.md)
