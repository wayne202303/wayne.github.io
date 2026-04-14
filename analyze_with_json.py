import json
from collections import defaultdict
from datetime import datetime
import subprocess
import sys

# 确保输出使用 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 直接运行 lark-cli 获取 JSON 数据
print("正在获取会议数据...")
result = subprocess.run(
    ['lark-cli', 'calendar', '+agenda', 
     '--start', '2026-01-10T00:00:00+08:00',
     '--end', '2026-04-10T23:59:59+08:00',
     '--format', 'json'],
    capture_output=True,
    text=True,
    encoding='utf-8'
)

if result.returncode != 0:
    print(f"获取数据失败: {result.stderr}")
    sys.exit(1)

# 解析 JSON
data = json.loads(result.stdout)
events = data.get('data', [])

# 统计数据
daily_stats = defaultdict(int)
weekday_stats = defaultdict(int)
weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

max_events = 0
max_day = None
day_events_map = defaultdict(list)

for event in events:
    summary = event.get('summary', '')
    
    # 跳过假期和休假
    if '假期' in summary or '休假' in summary:
        continue
    
    start_time = event.get('start_time', {}).get('datetime', '')
    if start_time:
        try:
            # 解析时间
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            date_key = dt.strftime('%Y-%m-%d')
            weekday = dt.weekday()  # 0=周一, 6=周日
            
            # 只统计工作日（周一到周五）
            if weekday < 5:
                daily_stats[date_key] += 1
                weekday_stats[weekday] += 1
                
                # 记录当天的会议
                time_str = dt.strftime('%H:%M')
                day_events_map[date_key].append((time_str, summary))
                
                # 记录最多会议的一天
                if daily_stats[date_key] > max_events:
                    max_events = daily_stats[date_key]
                    max_day = date_key
        except Exception as e:
            pass

print("=" * 60)
print("过去3个月会议统计（按工作日）")
print("=" * 60)
print()

# 按工作日统计
print("按星期统计：")
print("-" * 40)
total_events = 0
for i in range(5):
    count = weekday_stats.get(i, 0)
    total_events += count
    print(f"  {weekday_names[i]}: {count} 个会议")

print()
print("-" * 40)
print(f"总计：{total_events} 个工作日会议")
print(f"统计期间：2026-01-10 至 2026-04-10")
print()

# 会议最多的一天
if max_day:
    print("=" * 60)
    print("会议最多的一天：")
    print("=" * 60)
    
    try:
        max_dt = datetime.strptime(max_day, '%Y-%m-%d')
        weekday_idx = max_dt.weekday()
        print(f"日期：{max_day} ({weekday_names[weekday_idx]})")
        print(f"会议数量：{max_events} 个")
        print()
        
        print("当天会议列表：")
        print("-" * 40)
        day_events = day_events_map.get(max_day, [])
        day_events.sort()  # 按时间排序
        for idx, (time, summary) in enumerate(day_events, 1):
            print(f"  {idx}. [{time}] {summary}")
    except Exception as e:
        print(f"错误: {e}")
