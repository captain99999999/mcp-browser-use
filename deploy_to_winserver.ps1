# winserver 部署更新脚本
# 在 D:\browser-projects\use-browser 上执行此脚本

# 设置错误处理
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " WinServer MCP Server 部署更新" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ROOT = "D:\browser-projects\use-browser"
$GIT_BRANCH = "fev"
$VENV_ROOT = "$PROJECT_ROOT\.venv"
$PYTHON_EXE = "$VENV_ROOT\Scripts\python.exe"

Write-Host "📍 1. 检查项目路径..." -ForegroundColor Yellow
if (-not (Test-Path $PROJECT_ROOT -PathType Container)) {
    Write-Host "❌ 错误: 项目路径不存在: $PROJECT_ROOT" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 项目路径: $PROJECT_ROOT" -ForegroundColor Green

Write-Host "📍 2. 检查虚拟环境..." -ForegroundColor Yellow
if (-not (TestPath $VENV_ROOT -PathType Container)) {
    Write-Host "❌ 虚拟环境不存在: $VENV_ROOT" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 虚拟环境: $VENV_ROOT" -ForegroundColor Green

if (-not (TestPath $PYTHON_EXE -PathType Leaf)) {
    Write-Host "❌ Python 可执行文件不存在: $PYTHON_EXE" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python 可执行: $PYTHON_EXE" -ForegroundColor Green

Write-Host "📍 3. 拉取 fev 分支..." -ForegroundColor Yellow
Set-Location $PROJECT_ROOT

try {
    Push-Location $PROJECT_ROOT
    $gitBranch = git branch
    if ($gitBranch -ne "fev") {
        git checkout fev
        Write-Host "✓ 切换到 fev 分支" -ForegroundColor Green
    }
    git fetch origin
    git pull origin fev
    Write-Host "✓ 成功拉取 fev 分支更新" -ForegroundColor Green
    Write-Host "   最新提交: $(git log --oneline -1)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Git 操作失败: $_" -ForegroundColor Red
    Write-Host "   请手动执行以下命令:" -ForegroundColor Yellow
    Write-Host "   cd $PROJECT_ROOT" -ForegroundColor Yellow
    Write-Host "   git fetch origin" -ForegroundColor Yellow
    Write-Host "   git checkout fev" -ForegroundColor Yellow
    Write-Host "   git pull origin fev" -ForegroundColor Yellow
    exit 1
}

Write-Host "📍 4. 检查服务状态..." -ForegroundColor Yellow
$PORT = "8383"
$PORT_PROCESS = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue | Select-Object -ExpandProperty LocalAddress, LocalPort, State, OwningProcess | ForEachObject { if $_.OWNINGPROCESS.ProcessName -like "*python*" -or $_.OWNINGPROCESS.ProcessName -like "*mcp*"} }

if ($PORT_PROCESS) {
    $PID = $PORT_PROCESS.OwningProcess.Id
    Write-Host "⚠️  警告: 端口 $PORT 已被占用 (PID: $PID)" -ForegroundColor Yellow
    Write-Host "   需要先停止现有服务" -ForegroundColor Yellow
    Write-Host "   可以使用以下命令:" -ForegroundColor Yellow
    Write-Host "     taskkill /F /PID $PID" -ForegroundColor Yellow
    Write-Host "     或通过任务管理器停止" -ForegroundColor Yellow
    Write-Host "   ⚠️ 暂时跳过服务重启" -ForegroundColor Yellow
} else {
    Write-Host "✓ 端口 $PORT 未被占用" -ForegroundColor Green
}

Write-Host "📍 5. 检查新工具文件..." -ForegroundColor Yellow
$SEARCH_FILE = "$PROJECT_ROOT\search.py"
if (-not (Test-Path $SEARCH_FILE -PathType Leaf)) {
    Write-Host "❌ 搜索模块文件不存在: $SEARCH_FILE" -ForegroundColor Red
    Write-Host "   请检查文件传输是否完成" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ 搜索模块已就绪" -ForegroundColor Green

# 验证 server.py 中包含新工具
Write-Host "📍 6. 检查新工具导入..." -ForegroundColor Gray
if (Select-String -Path "$PROJECT_ROOT\server.py" -Pattern "from mcp_server_browser_use.search import" -SimpleMatch) {
    Write-Host "✓ 搜索模块导入已存在" -ForegroundColor Green
} else {
    Write-Host "❌ 搜索模块导入不存在" -ForegroundColor Red
    Write-Host "   可能需要手动修改 server.py 文件" -ForegroundColor Yellow
    Write-Host "   查看方法: Get-Content $PROJECT_ROOT\server.py | Select-String -Pattern \"web_search|web_fetch\"" -ForegroundColor Yellow
    exit 1
}

Write-Host "📍 7. 检查新工具注册..." -ForegroundColor Gray
if (Select-String -Path "$PROJECT_ROOT\server.py" -Pattern "web_search|web_fetch" -SimpleMatch) {
    Write-Host "✓ 新工具已注册" -ForegroundColor Green
} else {
    Write-Host "❌ 新工具未找到" -ForegroundColor Red
    Write-Host "   可能需要手动修改 server.py 文件" -ForegroundColor Yellow
    exit 1
}

Write-Host "🎯 部署准备完成！" -ForegroundColor Green
Write-Host "" -ForegroundColor Gray
Write-Host "⏺ 按以下步骤完成部署:" -ForegroundColor Cyan
Write-Host "  1. 检查是否有服务运行（netstat -ano | findstr :8383）" -ForegroundColor White
Write-Host " 2. 如有运行中的服务，先停止" -ForegroundColor White
Write-Host " 3. 执行以下命令：" -ForegroundColor White
Write-Host "     cd D:\\browser-projects\\use-browser" -ForegroundColor Cyan
Write-Host "     & .venv\Scripts\\python.exe .venv\\bin\\uv.exe sync" -ForegroundColor White
Write-Host "  4. 启动服务：" -ForegroundColor Cyan
Write-Host "     & .venv\Scripts\\python.exe .venv\\bin\\uv.exe server" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Gray
Write-Host "  ⚠️  如遇到依赖问题：" -ForegroundColor Yellow
Write-Host "     执行: .venv\Scripts\\python.exe .venv\\bin\\uv.exe sync" -ForegroundColor White
Write-Host "  ⚠️  如遇服务启动失败：" -ForegroundColor Yellow
Write-Host "     查看日志: .venv\\Logs\\server.log" -ForegroundColor White
Write-Host "     检查端口冲突: netstat -ano | findstr :8383" -ForegroundColor White
Write-Host "" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  ✅ 部署脚本已更新，请手动执行！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Gray
Write-Host "⏺ 按以下步骤完成部署:" -ForegroundColor Cyan
Write-Host "  1. cd D:\\browser-projects\\use-browser" -ForegroundColor White
Write-Host "  2. & .venv\Scripts\\python.exe .venv\\bin\\uv.exe sync" -ForegroundColor White
Write-Host "  3. & .venv\Scripts\\python.exe .venv\\bin\\uv.exe server"  或重新启动服务" -ForegroundColor White
Write-Host "" -ForegroundColor Gray
Write-Host "⚠️  如遇到依赖问题：" -ForegroundColor Yellow
Write-Host "     执行: .venv\\Scripts\\python.exe .venv\\bin\\uv.exe sync" -ForegroundColor White
Write-Host "  ⚠️  如遇服务启动失败:" -ForegroundColor Yellow
Write-Host "     查看日志: .venv\\Logs\\server.log" -ForegroundColor White
Write-Host "  ⚠️  如遇端口冲突:" -ForegroundColor Yellow
Write-Host "     netstat -ano | findstr :8383" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  ✅ 部署脚本已更新，请手动执行！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Gray
Write-Host "✅ 以下手动验证命令：" -ForegroundColor Green
Write-Host "  web_search 测试:" -ForegroundColor White
Write-Host '    {\"name\": \"web_search\", \"arguments\": {\"query\": \"Python async\", \"max_results\": 5}}' -ForegroundColor White
Write-Host "  web_fetch 测试:" -ForegroundColor White
Write-Host '    {\"name\": \"web_fetch\", \"arguments\": {\"url\": \"https://example.com\", \"output_format\": \"text\"}}' -ForegroundColor White
Write-Host "" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan