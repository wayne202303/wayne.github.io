# 简单的 MCP 检查脚本
Write-Host "=== MCP 简单检查 ===" -ForegroundColor Cyan
Write-Host ""

# 检查 Node 进程
Write-Host "1. 检查 Node.js 进程..." -ForegroundColor Yellow
$nodes = Get-Process | Where-Object {$_.ProcessName -like "*node*"}
if ($nodes) {
    Write-Host "找到 $($nodes.Count) 个 Node 进程" -ForegroundColor Green
} else {
    Write-Host "未找到 Node 进程" -ForegroundColor Yellow
}
Write-Host ""

# 检查配置文件
Write-Host "2. 检查配置文件..." -ForegroundColor Yellow
$configPath = "c:\Users\Admin\AppData\Roaming\Trae CN\User\mcp.json"
if (Test-Path $configPath) {
    Write-Host "配置文件存在" -ForegroundColor Green
    $content = Get-Content $configPath -Raw
    Write-Host "内容:" -ForegroundColor Cyan
    Write-Host $content
} else {
    Write-Host "配置文件不存在" -ForegroundColor Red
}
Write-Host ""

# 检查环境变量
Write-Host "3. 检查环境变量..." -ForegroundColor Yellow
$path = $env:PATH
if ($path -like "*node*") {
    Write-Host "PATH 包含 node.js" -ForegroundColor Green
} else {
    Write-Host "PATH 中未找到 node.js" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "检查完成！" -ForegroundColor Green
Write-Host ""
Write-Host "建议：" -ForegroundColor Yellow
Write-Host "1. 在 Trae 中按 F12 打开开发者工具"
Write-Host "2. 查看 Console 标签的错误"
Write-Host "3. 尝试以管理员身份运行 Trae"
