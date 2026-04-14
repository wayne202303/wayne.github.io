import json
import os
from datetime import datetime

# 配置
TEXT_FILE = 'wenzhang.xls'
POSTS_JSON = 'blog/data/posts.json'

# 读取现有的文章
def load_existing_posts():
    if os.path.exists(POSTS_JSON):
        with open(POSTS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# 读取文本文件
def load_text_data():
    try:
        with open(TEXT_FILE, 'r', encoding='gbk', errors='ignore') as f:
            lines = f.readlines()
        
        # 跳过第一行标题
        if len(lines) > 1:
            data = []
            for line in lines[1:]:
                line = line.strip()
                if line:
                    # 分割行数据
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        time_str = parts[0]
                        title = parts[1]
                        content = '\t'.join(parts[2:])
                        data.append((time_str, title, content))
            
            print(f"成功读取文本文件，共 {len(data)} 条记录")
            return data
        else:
            print("文件为空或只有标题行")
            return []
    except Exception as e:
        print(f"读取文本文件失败：{str(e)}")
        return []

# 转换为文章格式
def convert_to_posts(data, existing_posts):
    new_posts = []
    start_id = len(existing_posts) + 1
    
    for index, (time_str, title, content) in enumerate(data):
        # 处理日期
        try:
            # 尝试解析时间字符串
            date_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            date_str = date_obj.strftime('%Y-%m-%dT%H:%M:%S')
        except:
            date_str = datetime.now().strftime('%Y-%m-%dT10:00:00')
        
        # 生成 slug
        slug = title.lower().replace(' ', '-').replace('\n', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # 处理摘要
        excerpt = content[:100] + '...' if len(content) > 100 else content
        
        # 创建文章对象
        post = {
            "id": start_id + index,
            "title": title,
            "slug": slug,
            "date": date_str,
            "category": "默认分类",
            "tags": ["默认"],
            "excerpt": excerpt,
            "content": content
        }
        
        new_posts.append(post)
    
    return new_posts

# 保存到 JSON 文件
def save_posts(posts):
    with open(POSTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"成功保存 {len(posts)} 篇文章到 {POSTS_JSON}")

# 主函数
def main():
    print("开始从文本文件导入文章...")
    
    # 加载现有文章
    existing_posts = load_existing_posts()
    print(f"现有文章数量：{len(existing_posts)}")
    
    # 加载文本数据
    data = load_text_data()
    if not data:
        return
    
    # 转换为文章格式
    new_posts = convert_to_posts(data, existing_posts)
    print(f"新导入文章数量：{len(new_posts)}")
    
    # 合并并保存
    all_posts = existing_posts + new_posts
    save_posts(all_posts)
    
    print("\n导入完成！")
    print(f"总共 {len(all_posts)} 篇文章")
    print(f"新增 {len(new_posts)} 篇文章")

if __name__ == "__main__":
    main()
