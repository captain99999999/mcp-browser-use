# mcp-browser-use 内部定制版

基于上游 [Saik0s/mcp-browser-use](https://github.com/Saik0s/mcp-browser-use) 的内部定制，主要增强协作任务管理。

## 项目定位

- **上游**: https://github.com/Saik0s/mcp-browser-use
- **分支策略**: fev 分支进行本地开发，按需同步上游 main
- **核心定制**: Handover Lock 机制（暂停/恢复/操作员锁定）

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

### 按需同步步骤

```bash
# 1. 拉取上游更新
git fetch upstream

# 2. 查看上游变更
git log --oneline upstream/main

# 3. 合并到 fev
git merge upstream/main

# 4. 解决冲突（如有）
# 重点检查：observability/models.py, server.py

# 5. 验证测试通过
uv run pytest

# 6. 提交合并
git commit -m "chore: sync with upstream main"
```

### 冲突处理优先级

1. **observability/models.py**: 保留本地 handover 字段，合并其他变更
2. **server.py**: 保留本地 pause/resume 工具，合并其他工具更新
3. **测试文件**: 合并上游测试，确保本地功能测试覆盖

## 部署配置

### Winserver 环境

- **位置**: `D:\browser-projects\use-browser\`
- **配置文件**: `config.json`, `.env`
- **端口**: 8383

### 环境变量

```bash
DEEPSEEK_API_KEY=sk-xxx
MCP_BROWSER_CDP_URL=http://127.0.0.1:9222
```

### 启动方式

```bash
# 使用 start-mcp.ps1 或 mcp-start.bat
cd D:\browser-projects
powershell -File start-mcp.ps1
```

## 参考文档

- **上游开发指南**: AGENTS.md
- **FastMCP 最佳实践**: FASTMCP_PREVENTION_STRATEGIES.md
- **上游 README**: README.md
- **部署指南**: DEPLOY.md