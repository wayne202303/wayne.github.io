# Trae MCP 状态检查脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Trae MCP 深度状态检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查当前运行的进程
Write-Host "[1/5] 检查 Node.js 和相关进程..." -ForegroundColor Yellow
$nodeProcesses = Get-Process | Where-Object {$_.ProcessName -like "*node*"}
$cmdProcesses = Get-Process | Where-Object {$_.ProcessName -like "*cmd*"}

if ($nodeProcesses) {
    Write-Host "找到 $($nodeProcesses.Count) 个 Node.js 进程：" -ForegroundColor Green
    $nodeProcesses | ForEach-Object {
        Write-Host "  - PID: $($_.Id), 启动时间: $($_.StartTime)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "未找到 Node.js 进程" -ForegroundColor Yellow
}

if ($cmdProcesses) {
    Write-Host "找到 $($cmdProcesses.Count) 个 cmd 进程" -ForegroundColor Green
}
Write-Host ""

# 2. 监控进程变化
Write-Host "[2/5] 准备监控进程变化..." -ForegroundColor Yellow
Write-Host "现在请在 Trae 中点击 MCP 服务器的「重试」按钮" -ForegroundColor Magenta
Write-Host "点击后，按任意键继续查看进程变化..." -ForegroundColor Magenta
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "检查进程变化..." -ForegroundColor Cyan
$newNodeProcesses = Get-Process | Where-Object {$_.ProcessName -like "*node*"}
$newCmdProcesses = Get-Process | Where-Object {$_.ProcessName -like "*cmd*"}

$nodeDiff = Compare-Object -ReferenceObject $nodeProcesses -DifferenceObject $newNodeProcesses -Property Id
$cmdDiff = Compare-Object -ReferenceObject $cmdProcesses -DifferenceObject $newCmdProcesses -Property Id

if ($nodeDiff) {
    Write-Host "检测到 Node.js 进程变化：" -ForegroundColor Green
    $nodeDiff | ForEach-Object {
        $action = if ($_.SideIndicator -eq "=>") { "新增" } else { "消失" }
        Write-Host "  - PID $($_.Id): $action" -ForegroundColor White
    }
} else {
    Write-Host "未检测到 Node.js 进程变化" -ForegroundColor Yellow
}

if ($cmdDiff) {
    Write-Host "检测到 cmd 进程变化：" -ForegroundColor Green
    $cmdDiff | ForEach-Object {
        $action = if ($_.SideIndicator -eq "=>") { "新增" } else { "消失" }
        Write-Host "  - PID $($_.Id): $action" -ForegroundColor White
    }
} else {
    Write-Host "未检测到 cmd 进程变化" -ForegroundColor Yellow
}
Write-Host ""

# 3. 检查环境变量
Write-Host "[3/5] 检查相关环境变量..." -ForegroundColor Yellow
$envVars = Get-ChildItem Env: | Where-Object {
    $_.Name -like "*NODE*" -or 
    $_.Name -like "*PROXY*" -or 
    $_.Name -eq "PATH"
}

if ($envVars) {
    Write-Host "找到以下相关环境变量：" -ForegroundColor Green
    $envVars | ForEach-Object {
        if ($_.Name -eq "PATH") {
            $paths = $_.Value -split ';' | Where-Object { $_ -like "*node*" }
            if ($paths) {
                Write-Host "  PATH (node 相关):" -ForegroundColor Cyan
                $paths | ForEach-Object { Write-Host "    - $_" -ForegroundColor DarkGray }
            }
        } else {
            Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor White
        }
    }
} else {
    Write-Host "未找到相关环境变量" -ForegroundColor Yellow
}
Write-Host ""

# 4. 再次验证配置文件
Write-Host "[4/5] 再次验证配置文件..." -ForegroundColor Yellow
$configPath = "c:\Users\Admin\AppData\Roaming\Trae CN\User\mcp.json"
if (Test-Path $configPath) {
    $configContent = Get-Content $configPath -Raw
    Write-Host "配置文件内容：" -ForegroundColor Green
    Write-Host $configContent -ForegroundColor DarkGray
    
    try {
        $config = $configContent | ConvertFrom-Json
        $mcpArgs = $config.mcpServers.bytetech.args
        Write-Host ""
        Write-Host "命令参数分析：" -ForegroundColor Cyan
        $fullCmd = "$($config.mcpServers.bytetech.command) $($mcpArgs -join ' ')"
        Write-Host "  完整命令: $fullCmd" -ForegroundColor White
        
        if ($mcpArgs -contains "--registry") {
            $regIndex = $mcpArgs.IndexOf("--registry")
            if ($regIndex + 1 -lt $mcpArgs.Count) {
                Write-Host "  Registry: $($mcpArgs[$regIndex + 1])" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "JSON 解析错误: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "配置文件不存在" -ForegroundColor Red
}
Write-Host ""

# 5. 提供后续步骤建议
Write-Host "[5/5] 建议的后续步骤：" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 打开 Trae 开发者工具（F12）" -ForegroundColor White
Write-Host "   - 查看 Console 标签的错误信息" -ForegroundColor DarkGray
Write-Host "   - 查看 Network 标签的请求" -ForegroundColor DarkGray
Write-Host ""
Write-Host "2. 尝试以管理员身份运行 Trae" -ForegroundColor White
Write-Host ""
Write-Host "3. 参考 MCP深度排查指南.txt 进行进一步排查" -ForegroundColor White
Write-Host ""
Write-Host "4. 如果需要，尝试修改配置文件使用不同的启动方式" -ForegroundColor White
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Magenta
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
