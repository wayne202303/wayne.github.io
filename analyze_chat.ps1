# PowerShell 脚本来分析群聊消息
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "过去一周（4月3日-4月10日）发言统计" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# 获取消息
$result = lark-cli im +chat-messages-list --chat-id oc_fd63f039bf199b9063618ebc67c0981d --start "2026-04-03T00:00:00+08:00" --end "2026-04-10T23:59:59+08:00" --format json

# 解析 JSON
$data = $result | ConvertFrom-Json
$messages = $data.data.items

# 统计
$stats = @{}

foreach ($msg in $messages) {
    $sender = $msg.sender
    $name = if ($sender.name) { $sender.name } else { $sender.id }
    
    if ($stats.ContainsKey($name)) {
        $stats[$name]++
    } else {
        $stats[$name] = 1
    }
}

Write-Host " 发言次数 | 用户名" -ForegroundColor Yellow
Write-Host ("-" * 40) -ForegroundColor DarkGray

# 排序并输出
$sorted = $stats.GetEnumerator() | Sort-Object Value -Descending
foreach ($item in $sorted) {
    $count = $item.Value
    $name = $item.Name
    Write-Host ("  {0,4:d}   | {1}" -f $count, $name) -ForegroundColor White
}

Write-Host ""
Write-Host ("-" * 40) -ForegroundColor DarkGray
Write-Host " 总计：$($messages.Count) 条消息，$($stats.Count) 位用户发言" -ForegroundColor Green
