import os
import sys
from pathlib import Path


def _resolve_mcp_src() -> str:
    root = Path(__file__).resolve().parent
    local_src = root / "mcp-browser-use" / "src"
    if local_src.exists():
        return str(local_src)
    return os.getenv("MCP_BROWSER_USE_SRC", r"D:\browser-projects\mcp-browser-use\src")


def main() -> None:
    sys.path.insert(0, _resolve_mcp_src())

    from mcp_server_browser_use.config import settings
    from mcp_server_browser_use.server import serve

    print("Starting mcp-browser-use server...")
    print(f"  LLM: {settings.llm.provider}/{settings.llm.model_name}")
    print(f"  CDP:  {settings.browser.cdp_url}")
    print(f"  HTTP: http://{settings.server.host}:{settings.server.port}/mcp")
    print()

    server = serve()
    server.run(transport="streamable-http", host=settings.server.host, port=settings.server.port)


if __name__ == "__main__":
    main()
