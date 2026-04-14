import json
from collections import defaultdict
from datetime import datetime

# 读取会议数据
with open('events.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

events = data.get('data', [])

# 统计数据
daily_stats = defaultdict(int)
weekday_stats = defaultdict(int)
weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

max_events = 0
max_day = None

all_days = set()

for event in events:
    # 跳过假期和全天事件（可能是假期）
    summary = event.get('summary', '')
    if '假期' in summary or '休假' in summary:
        continue
    
    start_time = event.get('start_time', {}).get('datetime', '')
    if start_time:
        try:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            date_key = dt.strftime('%Y-%m-%d')
            weekday = dt.weekday()  # 0=周一, 6=周日
            
            # 只统计工作日（周一到周五）
            if weekday < 5:
                daily_stats[date_key] += 1
                weekday_stats[weekday] += 1
                all_days.add(date_key)
                
                # 记录最多会议的一天
                if daily_stats[date_key] > max_events:
                    max_events = daily_stats[date_key]
                    max_day = date_key
        except:
            pass

print("=" * 60)
print("📊 过去3个月会议统计（按工作日）")
print("=" * 60)
print()

# 按工作日统计
print("📅 按星期统计：")
print("-" * 40)
for i in range(5):
    count = weekday_stats.get(i, 0)
    print(f"  {weekday_names[i]}: {count} 个会议")

print()
print("-" * 40)
print(f"📈 总计：{sum(weekday_stats.values())} 个工作日会议")
print(f"📅 统计期间：2026-01-10 至 2026-04-10")
print()

# 会议最多的一天
if max_day:
    print("=" * 60)
    print("🏆 会议最多的一天：")
    print("=" * 60)
    max_dt = datetime.strptime(max_day, '%Y-%m-%d')
    weekday_idx = max_dt.weekday()
    print(f"📅 日期：{max_day} ({weekday_names[weekday_idx]})")
    print(f"📊 会议数量：{max_events} 个")
    print()
    
    # 列出那天的所有会议
    print("📋 当天会议列表：")
    print("-" * 40)
    day_events = []
    for event in events:
        start_time = event.get('start_time', {}).get('datetime', '')
        if start_time and start_time.startswith(max_day):
            summary = event.get('summary', '(无标题)')
            if '假期' not in summary and '休假' not in summary:
                day_events.append((start_time, summary))
    
    # 按时间排序
    day_events.sort()
    for idx, (time, summary) in enumerate(day_events, 1):
        time_str = time[11:16]  # 只取 HH:MM
        print(f"  {idx}. [{time_str}] {summary}")
