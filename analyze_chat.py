import json
from collections import defaultdict
import subprocess
import sys

# 确保输出使用 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

chat_id = "oc_fd63f039bf199b9063618ebc67c0981d"
start_time = "2026-04-03T00:00:00+08:00"
end_time = "2026-04-10T23:59:59+08:00"

user_stats = defaultdict(int)
all_messages = []

page_token = ""
page_count = 0

print("正在获取群聊消息...")

while True:
    page_count += 1
    print(f"  获取第 {page_count} 页...")
    
    args = [
        'lark-cli', 'im', '+chat-messages-list',
        '--chat-id', chat_id,
        '--start', start_time,
        '--end', end_time,
        '--format', 'json'
    ]
    
    if page_token:
        args.extend(['--page-token', page_token])
    
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if result.returncode != 0:
        print(f"获取数据失败: {result.stderr}")
        break
    
    data = json.loads(result.stdout)
    messages = data.get('data', {}).get('items', [])
    
    if not messages:
        break
    
    for msg in messages:
        sender = msg.get('sender', {})
        user_id = sender.get('id', '')
        user_name = sender.get('name', user_id)  # 如果没有名字就用 id
        
        # 统计
        user_stats[user_name] += 1
        all_messages.append(msg)
    
    # 检查是否有更多页
    has_more = data.get('data', {}).get('has_more', False)
    page_token = data.get('data', {}).get('page_token', '')
    
    if not has_more or not page_token:
        break

print(f"\n共获取 {len(all_messages)} 条消息")
print()

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
print(f" 总计：{len(all_messages)} 条消息，{len(sorted_users)} 位用户发言")
