# 筛选项与响应结构参考

本文档记录各接口的可用筛选参数、枚举值，以及响应 JSON 结构，供展示与调试时参考。

---

## 社媒日报（GetResults）筛选项

`source_types`、`institutions`、`authors` 三个参数均为数组，传空数组 `[]` 表示不过滤。

### source_types 可选值

| 值 | 含义 |
|----|------|
| `"大佬本人"` | 行业大佬/研究者本人发帖 |
| `"模型公司"` | 模型公司官方账号发帖 |

### institutions 可选值

| 值 |
|----|
| `"Google"` |
| `"OpenAI"` |
| `"Runway"` |
| `"minimax"` |
| `"xAI"` |
| `"腾讯"` |
| `"阿里"` |
| `"其他"` |

> 注：institutions 列表随数据动态变化，上述为已观测到的值。`authors` 字段同理，来自 `source.name`，为动态值，需先调用接口获取。

### 过滤示例

```bash
# 只看 Google 和 OpenAI 的大佬本人发帖
python3 scripts/sensight.py daily_social \
  --date 2026-03-05 \
  --source_types "大佬本人" \
  --institutions "Google" "OpenAI"
```

---

## 各接口响应数据结构

### GetEventBoard（获取热榜）

**数据访问路径**：`response.data[]`

```json
{
  "TopRank": 1,
  "Title": "中美就一些议题取得初步共识",
  "Heat": 12096044,
  "HeatRise": 0,
  "Sentiment": "NEUTRAL",
  "Tag": "owls_others",
  "TagName": "其他",
  "ExternalLink": "https://www.douyin.com/search/...",
  "Id": "16241400976813747175",
  "TimeInBoard": 49579,
  "Extra": "{}"
}
```

> 展示时用 `TopRank` 排序，显示格式：`{TopRank}. {Title}（热度 {Heat}）`；`Sentiment` 枚举：`POSITIVE` / `NEUTRAL` / `NEGATIVE`。

---

### SearchEvents（搜索热点事件）

**数据访问路径**：`response.data[]`

```json
{
  "event_id": "1010155534361856360",
  "title": "小米发布最新MiMo大模型",
  "start_time": "2025-12-17 16:00:00",
  "end_time": "2025-12-18 10:00:00",
  "score": 7780973,
  "summary": "",
  "url": "https://www.douyin.com/search/...",
  "ranking_name": "抖音",
  "ranking_id": "4081",
  "index": 17
}
```

> `summary` 可能为空字符串，展示时按 `title` + 来源（`ranking_name`）+ 时间（`start_time`）呈现；结果已按 `score` 降序排列。

---

### GetResults（社媒日报）

**数据访问路径**：`response.data.posts[]`

```json
{
  "id": 6279014,
  "source": {
    "id": 1490,
    "name": "Natasha Jaques",
    "avatar": "https://...",
    "institution": "Google",
    "source_type": "大佬本人",
    "job_title": ""
  },
  "content": "原文内容",
  "translate_content": "中文翻译",
  "created_at": 1772664976,
  "category": "技术趋势与前沿研究",
  "url": "https://x.com/...",
  "like_count": 0,
  "repost_count": 10,
  "view_count": 0
}
```

**返回结构还包含**：
- `data.topics[]`：热点话题列表，每个话题含 `title` 和关联的 `post_ids`

---

### ListPapers（论文日报）

**数据访问路径**：`response.data.data[]`（注意双层 `data`）

```json
{
  "title": "论文英文标题",
  "translated_title": "论文中文标题",
  "authors": ["作者1", "作者2"],
  "abstract": "英文摘要",
  "translated_abstract": "中文摘要",
  "url": "https://arxiv.org/...",
  "publish_time": 1741132800
}
```

---

### ListBlogs（博客日报）

**数据访问路径**：`response.data.data[]`（注意双层 `data`）

```json
{
  "post_id": 2574120,
  "source": {
    "name": "OpenAI",
    "institution": "OpenAI",
    "source_type": "rss"
  },
  "title": "博客英文标题",
  "translated_title": "博客中文标题",
  "summary": "英文摘要",
  "translated_summary": "中文摘要",
  "url": "https://openai.com/...",
  "publish_time": 1741222800
}
```

---

### GetWeeklyFeatured（本周焦点模型）

**数据访问路径**：`response.data.featured_events[]`

```json
{
  "id": 47,
  "model_series": "Gemini 3",
  "model_version_name": "Gemini 3.1 Flash-Lite",
  "organization": "Google",
  "logo_url": "https://...",
  "summary": "模型发布摘要（中文）",
  "publish_time": 1772555640000,
  "tags": ["最快", "最具成本效率", "规模化智能"],
  "url": "https://blog.google/..."
}
```

> 注：`publish_time` 为毫秒级时间戳。

---

### GetModelSentiment（模型口碑）

**数据访问路径**：
- `response.data.ai_summary`：字符串，AI 生成的整体舆情摘要
- `response.data.comments[]`：精选社区评论列表

```json
{
  "id": 144346,
  "content": "评论原文",
  "summary": "评论摘要",
  "platform": "微信公众号",
  "author_name": "作者名",
  "author_avatar": "https://...",
  "publish_time": 1772383149000,
  "mentioned_models": ["Claude Code", "Gemini 3"],
  "original_url": "https://..."
}
```

**常见 `platform` 值**：`"微信公众号"`、`"Twitter"`、`"微博"` 等。

---

### SocialSearch（社媒搜索）

**顶层结构**：`{ "BaseResp": { "StatusCode": 0 }, "items": [...] }`
**数据访问路径**：`response.items[]`

```json
{
  "content": "我觉得DeepSeek没有以前聪明了 为什么？#DeepSeek",
  "title": "DeepSeek",
  "url": "https://www.xiaohongshu.com/discovery/item/...",
  "user_name": "63393abb0000000018029351",
  "publish_time": "2026-03-15T10:45:31Z",
  "score": 0.8378
}
```

> `publish_time` 为 **ISO 8601 字符串**（UTC），展示时转为本地时间；`user_name` 可能是数字 UID；无 `platform`/`like_count` 等字段。

---

### SearchAuthorPosts（作者动态）

响应结构及展示规范详见 [author-posts-guide.md](author-posts-guide.md)。