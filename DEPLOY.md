# Winserver 部署指南

## 项目结构

```
D:\browser-projects\
├── mcp-browser-use/     # 源码（来自上游）
└── use-browser/         # 运行环境
    ├── .env            # 环境变量
    ├── config.json     # MCP 配置
    └── start_mcp.py    # 启动脚本
```

## 配置文件说明

### .env

```env
DEEPSEEK_API_KEY=sk-xxx
```

### config.json 关键配置

```json
{
  "llm": {
    "provider": "deepseek",
    "model_name": "deepseek-chat"
  },
  "browser": {
    "headless": false,
    "cdp_url": "http://127.0.0.1:9222"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8383
  }
}
```

## 启动方式

```bash
cd D:\browser-projects
powershell -File start-mcp.ps1
# 或
mcp-start.bat
```

## 检查运行状态

```bash
# 检查 8383 端口
netstat -ano | findstr :8383

# 查看日志
tail -f D:\browser-projects\use-browser\logs\*.log
```

## 本地定制功能

### Handover Lock 工具

部署后支持以下 MCP 工具：

- `task_pause` - 暂停运行中的任务
- `task_resume` - 恢复暂停的任务
- `task_cancel` - 取消任务（带操作员锁定检查）

这些工具会自动记录审计信息到 SQLite 数据库。

## 故障排查

### 服务无法启动

1. 检查端口 8383 是否被占用
2. 确认 DeepSeek API Key 有效
3. 检查 Chrome CDP 连接（如使用外部浏览器）

### 权限问题

确保启动脚本有执行权限：
```bash
icacls start-mcp.ps1 /grant Administrator:F
```

### 日志位置

```
D:\browser-projects\use-browser\logs\
├── server.log
└── error.log
```