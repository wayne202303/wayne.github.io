import json
import pandas as pd
from datetime import datetime
import os

# 配置
EXCEL_FILE = 'wenzhang.xls'
POSTS_JSON = 'blog/data/posts.json'

# 读取现有的文章
def load_existing_posts():
    if os.path.exists(POSTS_JSON):
        with open(POSTS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# 读取 Excel 文件
def load_excel_data():
    try:
        # 尝试不同的引擎
        engines = ['openpyxl', 'xlrd']
        for engine in engines:
            try:
                df = pd.read_excel(EXCEL_FILE, engine=engine)
                print(f"成功读取 Excel 文件，共 {len(df)} 条记录")
                return df
            except:
                continue
        print("无法读取 Excel 文件，请检查文件格式")
        return None
    except Exception as e:
        print(f"读取 Excel 文件失败：{str(e)}")
        return None

# 转换为文章格式
def convert_to_posts(df, existing_posts):
    new_posts = []
    start_id = len(existing_posts) + 1
    
    for index, row in df.iterrows():
        # 提取字段
        title = str(row.get('标题', f'文章{index + 1}')).strip()
        content = str(row.get('内容', '')).strip()
        category = str(row.get('分类', '未分类')).strip()
        tags = str(row.get('标签', '')).strip()
        excerpt = str(row.get('摘要', content[:100] + '...' if len(content) > 100 else content)).strip()
        
        # 处理日期
        date = row.get('日期')
        if isinstance(date, pd.Timestamp):
            date_str = date.strftime('%Y-%m-%dT10:00:00')
        else:
            date_str = datetime.now().strftime('%Y-%m-%dT10:00:00')
        
        # 生成 slug
        slug = title.lower().replace(' ', '-').replace('\n', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # 处理标签
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        if not tags_list:
            tags_list = ['默认']
        
        # 创建文章对象
        post = {
            "id": start_id + index,
            "title": title,
            "slug": slug,
            "date": date_str,
            "category": category,
            "tags": tags_list,
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
    print("开始从 Excel 导入文章...")
    
    # 加载现有文章
    existing_posts = load_existing_posts()
    print(f"现有文章数量：{len(existing_posts)}")
    
    # 加载 Excel 数据
    df = load_excel_data()
    if df is None:
        return
    
    # 转换为文章格式
    new_posts = convert_to_posts(df, existing_posts)
    print(f"新导入文章数量：{len(new_posts)}")
    
    # 合并并保存
    all_posts = existing_posts + new_posts
    save_posts(all_posts)
    
    print("\n导入完成！")
    print(f"总共 {len(all_posts)} 篇文章")
    print(f"新增 {len(new_posts)} 篇文章")

if __name__ == "__main__":
    main()
