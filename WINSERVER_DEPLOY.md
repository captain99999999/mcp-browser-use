# WinServer 部署指南

## 📍 项目位置

**实际部署路径**: `C:\Users\Administrator\`  
**用户主目录** - 包含项目相关文件

## ⚠️ 问题排查

由于 SSH 连接不稳定（编码问题），请按以下步骤手动执行。

---

## 📋 部署步骤

### 步骤 1: 确认当前状态

```powershell
# 检查虚拟环境
cd C:\Users\Administrator
Test-Path .venv -PathType Container

# 查看 Git 状态
git remote -v
git branch
git log --oneline -3
```

**如果看到 fev 分支**：
```bash
git checkout fev
git pull origin fev
```

### 步骤 2: 检查虚拟环境

```powershell
cd C:\Users\Administrator
.venv\Scripts\python.exe --version
```

**应该显示**: `Python 3.11` 或更高版本

### 步骤 3: 检查搜索文件

```powershell
cd C:\Users\Administrator
Test-Path .venv\search.py
```

**如果文件不存在**，检查是否在项目子目录：
```powershell
# 检查是否在其他位置
gci C:\Users\Administrator -Recurse -File -Filter "*.py" | Select-String Name | Select-Object FullName | Where-Object { $_}
```

### 步骤 4: 检查并修改 server.py

```powershell
# 查看 server.py 文件开头
Get-Content C:\Users\Administrator\server.py | Select-Object -First 20 | Select-Object -Object -AsString
```

**检查以下导入是否已添加**：
```python
from mcp_server_browser_use.search import ...
```

**如果缺少**，需要在 server.py 添加：
```python
from mcp_server_browser_use.search import (
    generate_search_queries,
    search_duckduckgo,
    deduplicate_results,
    SearchResult,
)
```

### 步骤 5: 执行依赖更新

```powershell
# 在项目根目录执行
cd C:\Users\Administrator

# 检查是否在 git 仓库中
git rev-parse --is-inside-work-tree

# 如果不在，创建虚拟环境
python -m venv venv

# 更新依赖
& .venv\Scripts\python.exe -m uv sync
```

### 步骤 6: 重启 MCP 服务器

```powershell
# 检查服务状态
netstat -ano | findstr :8383

# 如果服务运行，先停止
taskkill /F /PID <进程ID>

# 启动服务
cd C:\Users\Administrator
& .venv\Scripts\python.exe .venv\bin\uv.exe server
```

---

## 🧪 验证部署

### 1. 检查工具是否在列表中

访问 http://winserver:8383/dashboard

在"工具"选项卡中应该看到：
- `web_search`
- `web_fetch`

### 2. 测试 web_search

```json
{
  "name": "web_search",
  "arguments": {
    "query": "Python 3.12 新特性",
    "max_results": 5
  }
}
```

### 3. 测试 web_fetch

```json
{
  "name": "web_fetch",
  "arguments": {
    "url": "https://example.com",
    "output_format": "text"
  }
}
```

### 4. 检查日志

如果服务异常，查看：
```bash
# 查看 .venv\Logs\server.log
# 或查看项目根目录下的日志文件
```

---

## 🔧 常见问题

### 错误：文件不存在

**原因**：搜索模块或 server.py 未更新

**解决**：
1. 从本地上传缺失的文件
2. 手动添加缺少的导入

### 错误：依赖更新失败

**原因**：网络问题或包版本冲突

**解决**：
```powershell
python -m uv sync
# 或
python -m uv update
```

### 错误：服务启动失败

**原因**：端口冲突、配置问题或缺少 API Key

**解决**：
```bash
# 检查端口占用
netstat -ano | findstr :8383

# 检查配置
cat .env | Select-String "API"

# 检查日志
.venv\Logs\server.log
```

### 错误：工具不可见

**原因**：server.py 未正确更新

**解决**：
1. 确认 server.py 中包含搜索模块导入
2. 重新启动服务
3. 检查日志确认工具已注册

---

## 📝 项目相关文件

**主目录关键文件**：
- `mcp_entrypoint.py` - 入口文件
- `mcp_server.log` - 服务日志
- `mcp_startup.log` - 启动日志
- `config.json` - 配置文件（可能在子目录）

**可能的项目目录**：
- `skills/` - 技能存储目录
- `observability/` - 可观测性模块

---

## 🔄 服务管理

### 重启服务

```bash
taskkill /F /PID <进程ID>
cd C:\Users\Administrator
& .venv\Scripts\python.exe .venv\bin\uv.exe server
```

### 查看日志

```bash
# 实时日志
tail -f .venv\Logs\server.log

# 历史日志
dir .venv\Logs\
ls -lt .venv\Logs\*.log | Select-Object FullName | Select-Object -LastWriteTime | Sort-Object FullName
```

---

## 🎯 技能路径配置

根据之前的调查，可能配置文件位置：
- 主目录：`~/.config/mcp-server-browser-use/config.json`
- 子目录：可能存在于某个子目录下

---

## 💡 备份建议

重要文件应该备份：
- `config.json`
- `.env`
- `skills/` 目录

---

## ✅ 部署完成指标

- ✅ 新工具已添加
- ✅ 进度追踪支持
- ✅ 错误处理完善
- ✅ 部署文档完整

---

**需要我进一步协助吗？** 例如：手动添加文件、检查具体错误等。