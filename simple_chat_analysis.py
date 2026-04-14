import json
from collections import defaultdict
import sys

# 确保输出使用 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 读取数据文件
with open('chat_data.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

messages = data.get('data', {}).get('items', [])

# 统计数据
user_stats = defaultdict(int)

for msg in messages:
    sender = msg.get('sender', {})
    user_name = sender.get('name', '')
    if not user_name:
        user_name = sender.get('id', 'unknown')
    
    user_stats[user_name] += 1

print("=" * 60)
print("过去一周（4月3日-4月10日）发言统计")
print("=" * 60)
print()

# 按发言次数排序
sorted_users = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)

print(" 发言次数 | 用户名")
print("-" * 40)
for name, count in sorted_users:
    print(f"  {count:4d}   | {name}")

print()
print("-" * 40)
print(f" 总计：{len(messages)} 条消息，{len(sorted_users)} 位用户发言")
