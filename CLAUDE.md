# mcp-browser-use（内部 fork）

基于上游 [Saik0s/mcp-browser-use](https://github.com/Saik0s/mcp-browser-use) 的内部定制 fork。

## 仓库拓扑

| 角色 | 地址 | 用途 |
|---|---|---|
| **上游（upstream）** | `github.com/Saik0s/mcp-browser-use` | 原始开源项目，**不可直接推送** |
| **本 fork** | `github.com/captain99999999/mcp-browser-use` | **唯一的推送目标** |
| **本地工作目录** | `e:\项目代码\mcp-browser-use` | 开发机工作区 |
| **winserver 部署目录** | `D:\browser-projects\mcp-browser-use` | 生产环境，git origin 已指向本 fork |

**分支策略**：
- `main` 跟上游同步（只读，不直接开发）
- `fev` 是本 fork 的开发分支，**所有改动都在 fev 上进行**
- 远端默认运行分支：`fev`

## 项目定位

- **核心定制**：Handover Lock 机制（任务暂停/恢复/操作员锁定），便于多操作员协作
- **新增工具**：`web_search` / `web_fetch`（基于 Google 解析的搜索与页面抓取）
- **目标场景**：MCP 客户端（Claude/Copilot 等）通过 streamable-http 调用本服务，自动化浏览器任务

## 本地开发流程

### 环境准备

```bash
uv sync
uv run playwright install chromium
```

### 开发检查（遵循上游规范）

```bash
uv sync && uv run ruff format . && uv run ruff check . && uv run pyright && uv run pytest
```

### 核心定制说明

**Handover Lock 功能**：
- 支持 `task_pause` 和 `task_resume` MCP 工具
- 审计元数据自动持久化到 SQLite
- 操作员锁定防止并发冲突

**使用场景**：
- 多操作员协作时任务交接
- 长时间运行任务的临时暂停
- 操作审计和追溯

## 上游同步策略

> **仅在确实需要合入上游更新时执行**。本 fork 已独立演进，不应频繁同步。

```bash
# 1. 确保本地 fev 工作区干净
git status

# 2. 拉取上游更新（用临时 remote 避免污染主仓库）
git remote add upstream https://github.com/Saik0s/mcp-browser-use.git 2>/dev/null \
  || git remote set-url upstream https://github.com/Saik0s/mcp-browser-use.git
git fetch upstream

# 3. 查看上游 main 上的新提交
git log --oneline main..upstream/main

# 4. 合并到 fev
git checkout fev
git merge upstream/main

# 5. 解决冲突（如有）—— 见下方优先级

# 6. 验证测试通过
uv run pytest

# 7. 推送到本 fork
git push origin fev
```

### 冲突处理优先级

1. **`src/mcp_server_browser_use/observability/models.py`**: 保留本地 handover 字段，合并其他变更
2. **`src/mcp_server_browser_use/server.py`**: 保留本地 `pause` / `resume` / `web_search` / `web_fetch` 工具，合并其他工具更新
3. **`src/mcp_server_browser_utils/`**: 本地新增子包（Google 解析 + 查询生成），上游没有，保留
4. **测试文件**: 合并上游测试，确保本地 `tests/integration_tests/test_web_tools.py` 仍能跑通

## 部署配置

### Winserver 部署

| 项 | 值 |
|---|---|
| 部署路径 | `D:\browser-projects\mcp-browser-use\` |
| 启动脚本 | `D:\browser-projects\use-browser\start_mcp.py`（用 use-browser 的 venv） |
| 端口 | `8383`（HTTP / mcp） |
| git origin | `git@github.com:captain99999999/mcp-browser-use.git` |
| 工作分支 | `fev` |
| 配置文件 | winserver 的 `D:\browser-projects\use-browser\.env`（**不在本仓库**） |
| API Key | `DEEPSEEK_API_KEY`（在 `.env` 中，**禁止入库**） |
| CDP 目标 | `http://127.0.0.1:9222`（连 browser-pool 的 9222 端口） |

### 启动 / 重启流程

```powershell
# 在 winserver 的 RDP 桌面上执行（必须桌面会话，SSH 的 Start-Process 无桌面）
ssh winserver "taskkill /F /PID <旧进程 PID>"
ssh winserver "D:\browser-projects\use-browser\.venv\Scripts\python.exe D:\browser-projects\use-browser\start_mcp.py"
```

### winserver git 同步流程

```bash
# 在 winserver 上：
cd D:\browser-projects\mcp-browser-use
git fetch origin
git reset --hard origin/fev    # 注意：会丢弃未提交修改
# 然后重启服务
```

> 部署目录历史上是从 Saik0s 仓库独立 clone 出来的，**已切到 captain99999999 fork**。如需重新拉取，先确认 `git remote -v` 是否指向 fork。

## 参考文档

| 文档 | 用途 |
|---|---|
| [AGENTS.md](AGENTS.md) | 上游贡献规范（lint / format / type-check / test）+ 本地补充 |
| [FASTMCP_PREVENTION_STRATEGIES.md](FASTMCP_PREVENTION_STRATEGIES.md) | FastMCP 常见坑和规避模式 |
| [README.md](README.md) | 用户面向文档（部署、配置、工具说明） |
| [.github/copilot-instructions.md](.github/copilot-instructions.md) | 工作区级 Copilot 指令（多项目背景） |