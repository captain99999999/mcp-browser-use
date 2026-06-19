---
applyTo: "**/deploy*.{ps1,sh,py,yml,yaml}"
---

# Deployment / config files

These files orchestrate the **winserver** (192.168.110.250) deployment. They run with elevated privileges and affect a live MCP service on port 8383.

## Hard rules

- **Never** modify `D:\browser-projects\mcp-browser-use\` files directly on winserver — that directory is meant to be a clean mirror of this repo
- **Never** commit secrets, API keys, or `.env` files
- **Never** restart the MCP service without warning — it kills in-flight browser tasks
- **Always** go through `git push origin fev` + `ssh winserver "git pull origin fev"` for code updates

## Safe restart pattern

```powershell
# 1. Find the running process
ssh winserver "netstat -ano | findstr :8383"

# 2. Kill it (in-flight tasks will fail)
ssh winserver "taskkill /F /PID <pid>"

# 3. Start fresh (MUST be in RDP desktop session, not pure SSH)
ssh winserver "D:\browser-projects\use-browser\.venv\Scripts\python.exe D:\browser-projects\use-browser\start_mcp.py"
```

## What this project does NOT have

- No `docker-compose.yml` (don't add one without explicit user approval)
- No `start-mcp.ps1` (the actual entry point is `D:\browser-projects\use-browser\start_mcp.py`)
- No system-level services (no systemd, no Windows Service) — service runs as a foreground Python process
