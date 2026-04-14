# PowerShell 脚本分析会议数据
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "📊 过去3个月会议统计（按工作日）" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# 获取会议数据
Write-Host "正在获取会议数据..." -ForegroundColor Yellow
$jsonData = lark-cli calendar +agenda --start "2026-01-10T00:00:00+08:00" --end "2026-04-10T23:59:59+08:00" --format json
$eventsObj = $jsonData | ConvertFrom-Json
$events = $eventsObj.data

Write-Host "共获取 $($events.Count) 条记录" -ForegroundColor Green
Write-Host ""

# 初始化统计
$dailyStats = @{}
$weekdayStats = @{0=0; 1=0; 2=0; 3=0; 4=0}
$weekdayNames = @("周一", "周二", "周三", "周四", "周五")
$maxEvents = 0
$maxDay = $null
$dayEventsMap = @{}

foreach ($event in $events) {
    $summary = $event.summary
    if ($summary -match "假期|休假") {
        continue
    }
    
    $startTime = $event.start_time.datetime
    if ($startTime) {
        try {
            $dt = [DateTime]::Parse($startTime)
            $dateKey = $dt.ToString("yyyy-MM-dd")
            $weekday = [int]$dt.DayOfWeek
            
            # 转换为 0=周一, 4=周五
            if ($weekday -eq 0) { $weekday = 6 }
            $weekday = $weekday - 1
            
            # 只统计工作日
            if ($weekday -ge 0 -and $weekday -le 4) {
                if (-not $dailyStats.ContainsKey($dateKey)) {
                    $dailyStats[$dateKey] = 0
                    $dayEventsMap[$dateKey] = @()
                }
                $dailyStats[$dateKey]++
                $weekdayStats[$weekday]++
                
                # 记录当天的会议
                $dayEventsMap[$dateKey] += @{
                    Time = $dt.ToString("HH:mm")
                    Summary = $summary
                }
                
                # 检查是否是最多会议的一天
                if ($dailyStats[$dateKey] -gt $maxEvents) {
                    $maxEvents = $dailyStats[$dateKey]
                    $maxDay = $dateKey
                }
            }
        } catch {
            # 忽略解析错误
        }
    }
}

# 输出按星期统计
Write-Host "📅 按星期统计：" -ForegroundColor Cyan
Write-Host ("-" * 40) -ForegroundColor DarkGray
$totalEvents = 0
for ($i = 0; $i -lt 5; $i++) {
    $count = $weekdayStats[$i]
    $totalEvents += $count
    Write-Host "  $($weekdayNames[$i]): $count 个会议" -ForegroundColor White
}

Write-Host ""
Write-Host ("-" * 40) -ForegroundColor DarkGray
Write-Host "📈 总计：$totalEvents 个工作日会议" -ForegroundColor Green
Write-Host "📅 统计期间：2026-01-10 至 2026-04-10" -ForegroundColor White
Write-Host ""

# 输出会议最多的一天
if ($maxDay) {
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "🏆 会议最多的一天：" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
    
    $maxDt = [DateTime]::Parse($maxDay)
    $weekdayIdx = [int]$maxDt.DayOfWeek
    if ($weekdayIdx -eq 0) { $weekdayIdx = 6 }
    $weekdayIdx = $weekdayIdx - 1
    
    Write-Host "📅 日期：$maxDay ($($weekdayNames[$weekdayIdx]))" -ForegroundColor White
    Write-Host "📊 会议数量：$maxEvents 个" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "📋 当天会议列表：" -ForegroundColor Cyan
    Write-Host ("-" * 40) -ForegroundColor DarkGray
    
    $dayEvents = $dayEventsMap[$maxDay] | Sort-Object { $_.Time }
    $idx = 1
    foreach ($ev in $dayEvents) {
        Write-Host "  $idx. [$($ev.Time)] $($ev.Summary)" -ForegroundColor White
        $idx++
    }
}
