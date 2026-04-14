import subprocess
import json
from datetime import datetime, timedelta

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    return result.stdout, result.stderr

def search_wiki():
    import tempfile
    import os
    
    # 创建临时 JSON 文件
    data = {"query": "", "page_size": 50}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f)
        temp_file = f.name
    
    try:
        cmd = f'lark-cli api POST /open-apis/wiki/v2/nodes/search --data @{temp_file}'
        stdout, stderr = run_command(cmd)
        try:
            return json.loads(stdout)
        except:
            print(f"搜索失败: {stderr}")
            return None
    finally:
        os.unlink(temp_file)

def get_file_statistics(obj_token, obj_type):
    import tempfile
    import os
    
    file_type_map = {
        1: 'doc',
        2: 'sheet',
        3: 'bitable',
        8: 'docx'
    }
    file_type = file_type_map.get(obj_type, 'docx')
    
    # 创建临时 JSON 文件
    params = {"file_type": file_type}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(params, f)
        temp_file = f.name
    
    try:
        cmd = f'lark-cli api GET /open-apis/drive/v1/files/{obj_token}/statistics --params @{temp_file}'
        stdout, stderr = run_command(cmd)
        try:
            result = json.loads(stdout)
            if result.get('code') == 0:
                return result['data']
        except:
            pass
        return None
    finally:
        os.unlink(temp_file)

def main():
    print("正在搜索知识库文章...")
    search_result = search_wiki()
    if not search_result or search_result.get('code') != 0:
        print("搜索失败")
        return
    
    items = search_result.get('data', {}).get('items', [])
    if not items:
        print("未找到文章")
        return
    
    print(f"找到 {len(items)} 篇文章，正在获取统计信息...\n")
    
    articles = []
    for i, item in enumerate(items, 1):
        title = item.get('title', '无标题')
        if not title:
            continue
            
        obj_token = item.get('obj_token')
        obj_type = item.get('obj_type')
        url = item.get('url', '')
        
        print(f"[{i}/{len(items)}] 正在获取: {title}")
        
        stats = get_file_statistics(obj_token, obj_type)
        if stats:
            statistics = stats.get('statistics', {})
            like_count = statistics.get('like_count', 0)
            like_count_today = statistics.get('like_count_today', 0)
            
            # 只计算最近一周的点赞数
            # 注意：API 只返回历史总点赞数和今日新增，没有按周统计
            # 我们先用总点赞数排序
            
            articles.append({
                'title': title,
                'url': url,
                'like_count': like_count,
                'like_count_today': like_count_today,
                'pv': statistics.get('pv', 0),
                'uv': statistics.get('uv', 0)
            })
    
    # 按点赞数排序
    articles.sort(key=lambda x: x['like_count'], reverse=True)
    
    print("\n" + "="*80)
    print("知识库文章点赞数排行（按总点赞数）")
    print("="*80)
    
    for i, article in enumerate(articles, 1):
        print(f"\n第 {i} 名:")
        print(f"  标题: {article['title']}")
        print(f"  链接: {article['url']}")
        print(f"  总点赞数: {article['like_count']}")
        print(f"  今日新增点赞: {article['like_count_today']}")
        print(f"  总阅读次数: {article['pv']}")
        print(f"  总阅读人数: {article['uv']}")
    
    print("\n" + "="*80)
    print(f"总计: {len(articles)} 篇文章")

if __name__ == "__main__":
    main()
