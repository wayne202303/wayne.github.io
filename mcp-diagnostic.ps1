# MCP 诊断脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MCP 服务器诊断工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Node.js
Write-Host "[1/7] 检查 Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Host "✅ Node.js 已安装: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Node.js 未安装" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Node.js 未安装" -ForegroundColor Red
}
Write-Host ""

# 2. 检查 npm
Write-Host "[2/7] 检查 npm..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version 2>$null
    if ($npmVersion) {
        Write-Host "✅ npm 已安装: $npmVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ npm 未安装" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ npm 未安装" -ForegroundColor Red
}
Write-Host ""

# 3. 检查 npx
Write-Host "[3/7] 检查 npx..." -ForegroundColor Yellow
try {
    $npxVersion = npx --version 2>$null
    if ($npxVersion) {
        Write-Host "✅ npx 已安装: $npxVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ npx 未安装" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ npx 未安装" -ForegroundColor Red
}
Write-Host ""

# 4. 检查网络连接
Write-Host "[4/7] 检查网络连接..." -ForegroundColor Yellow
try {
    $testUrl = "http://bnpm.byted.org/"
    $response = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ 可以访问 bnpm.byted.org" -ForegroundColor Green
    } else {
        Write-Host "⚠️  访问 bnpm.byted.org 状态码: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ 无法访问 bnpm.byted.org" -ForegroundColor Red
    Write-Host "   错误: $($_.Exception.Message)" -ForegroundColor DarkGray
}
Write-Host ""

# 5. 检查配置文件
Write-Host "[5/7] 检查 MCP 配置文件..." -ForegroundColor Yellow
$configPath = "c:\Users\Admin\AppData\Roaming\Trae CN\User\mcp.json"
if (Test-Path $configPath) {
    Write-Host "✅ 配置文件存在" -ForegroundColor Green
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        Write-Host "✅ JSON 格式正确" -ForegroundColor Green
        
        # 检查 registry 参数
        $args = $config.mcpServers.bytetech.args
        if ($args -contains "--registry" -and $args -contains "http://bnpm.byted.org/") {
            Write-Host "✅ registry 参数已正确配置" -ForegroundColor Green
        } else {
            Write-Host "❌ registry 参数缺失或不正确" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ JSON 格式错误: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "❌ 配置文件不存在: $configPath" -ForegroundColor Red
}
Write-Host ""

# 6. 测试 MCP 命令
Write-Host "[6/7] 测试 MCP 命令（可能需要几分钟）..." -ForegroundColor Yellow
Write-Host "   正在运行: npx -y --registry http://bnpm.byted.org/ @mcp_hub/cli@latest run @mcp_hub/bytetech" -ForegroundColor DarkGray
Write-Host "   注意：这个命令将启动 MCP 服务器，按 Ctrl+C 可以停止" -ForegroundColor DarkGray
Write-Host ""
Write-Host "按任意键开始测试，或按 Ctrl+C 跳过..." -ForegroundColor Magenta
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

try {
    Write-Host ""
    Write-Host "启动 MCP 服务器..." -ForegroundColor Cyan
    Write-Host "（服务器将运行 10 秒后自动停止）" -ForegroundColor DarkGray
    
    $process = Start-Process -FilePath "npx" -ArgumentList @("-y", "--registry", "http://bnpm.byted.org/", "@mcp_hub/cli@latest", "run", "@mcp_hub/bytetech") -NoNewWindow -PassThru
    
    Start-Sleep -Seconds 10
    
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        Write-Host "✅ MCP 服务器成功启动并运行了 10 秒" -ForegroundColor Green
    } else {
        Write-Host "❌ MCP 服务器启动失败，退出代码: $($process.ExitCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 测试过程中出错: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 7. 总结
Write-Host "[7/7] 诊断完成" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  建议操作：" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. 如果所有检查都通过，尝试重启 Trae" -ForegroundColor White
Write-Host "2. 在 Trae 中点击 MCP 服务器的「重试」按钮" -ForegroundColor White
Write-Host "3. 如仍有问题，查看 Trae 开发者工具的 Console 标签" -ForegroundColor White
Write-Host "4. 参考 MCP排查指南.txt 进行进一步排查" -ForegroundColor White
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Magenta
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
