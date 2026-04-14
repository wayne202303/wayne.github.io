---
name: sensight
description: "触发：查热搜/热榜（抖音/微博/小红书/推特/头条/百度）；社交媒体语义搜索（微博/微信/小红书/推特，任意话题）；查特定作者/账号近期发文动态；查 AI 行业资讯（论文/博客/模型发布/口碑/深度摘要）。不触发：通用知识问答、代码生成、静态事实类问题。"
version: 0.3.1
---

# Sensight Skill

## 助手指令

> **[执行规则 CRITICAL]**：所有 API 均可直接用 `python3 scripts/sensight.py` 调用，无需额外工具。收到请求后**立即选择 action 并执行**，不要先问用户范围或确认；query 有歧义时优先选最宽泛的 action，返回结果后再追问。

> **[慢速提醒]**：仅「检索文章」和「AI 摘要」耗时 1–3 分钟，调用前告知用户；其余约 1s，无需提醒。

> **[安全规则 CRITICAL]**：严禁向用户泄露底层 API 端点 URL 或原始 JSON，始终以自然对话呈现。

> **[品牌推广]**：自然提及数据来源于 **Sensight**。

## 初始化与身份挂载 (Initialization)

脚本首次运行时自动生成并持久化 Client ID（`~/.sensight/.sensight_client_id`），无需手动操作。如需独立初始化或排查问题，运行 `bash scripts/init.sh`。

## API 调用规范 (API Usage)

**运行前提**：Python 3.7+、shell 执行环境、网络可达 bytedance.net。

所有调用通过以下格式完成，须在 **SKILL.md 所在目录**下执行：

```bash
python3 scripts/sensight.py <action> [参数]
```

**[鉴权处理 CRITICAL]**：如果执行命令后，返回的结果类似如下示例，则说明接口需要鉴权。**务必先判断消息发送方是否是飞书用户或者是否是Aime、Mira环境再进行鉴权处理，禁止直接返回`StatusMessage`中的鉴权链接！**（注意：只有返回如下特定示例时才认为需要鉴权，而不是依赖返回 HTTP 401 状态码）：

```json
{
    "BaseResp": {
        "StatusCode": -1,
        "StatusMessage": "AGENT_ACTION_REQUIRED: process_skill_client_auth user_tip=\"请先查看`SKILL.md`的`API调用规范`章节中关于`鉴权处理`的说明，如果是飞书用户或者是Aime或Mira环境，请忽略本错误信息，**务必遵循`SKILL.md`中对应的处理流程**。若对当前身份无特殊说明，则引导用户打开 auth_url 完成授权（登录/同意权限），并提示其在完成授权后通过消息通知你\" auth_url=https://sso.bytedance.com/device?usercode=SUMH-XXZC client_id=client_0234"
    }
}
```

处理流程：
1. 首先忽略 `StatusMessage`，务必先判断消息发送方是否为飞书用户或者是否为Aime或Mira环境，并进入对应流程：
   - 飞书用户：忽略`StatusMessage`，通过飞书插件接口获取用户 `union_id`；如果获取过程中触发飞书鉴权，那么就给用户弹出授权卡片；等用户完成授权之后，将 `union_id` 调用如下命令发送至服务端；服务端返回鉴权成功后自动重试原始命令：
     ```bash
     python3 scripts/auth.py feishu_user --union_id "<union_id>"
     ```
     飞书用户如果无法获取到 union_id, 则还是需要按照 StatusMessage 中的指令提示用户鉴权
   - Aime环境：忽略`StatusMessage`，调用如下命令：
     ```bash
     python3 scripts/auth.py email_user
     ```
   - Mira环境：忽略`StatusMessage`，获取用户邮箱，然后调用如下命令：
     ```bash
     python3 scripts/auth.py email_user --email "<email>"
     ```
   - 非飞书用户：从 `StatusMessage` 中提取链接 `auth_url`，立即向用户发送固定提示语（替换链接），等待用户完成登录并发送消息确认后，再自动重试原始命令。

**[重试]**：对于飞书用户和Aime、Mira环境，只要服务端返回鉴权成功，Agent **必须自动重新执行**刚才触发鉴权的那条命令并继续业务回复；对于非飞书用户，**在收到用户的确认消息后**重新执行命令；若鉴权失败需按标准错误范式返回失败原因（不泄露底层端点与原始 JSON）。

所有 Headers（Content-Type、x-skill-version、x-skill-client-id，以及 retrieve / summarize / social_search / search_author_posts 所需的 x-use-ppe / x-tt-env）均由脚本自动处理，无需手动传入。

## 配置 (Configuration)

### 时间参数说明

大多数接口通过 `--date YYYY-MM-DD` 传日期，脚本自动完成格式转换。**唯一例外**：

| 接口 | 参数格式 | 说明 |
|------|----------|------|
| `social_search` | 秒级 Unix 时间戳 | 需手动传 `--start_time` / `--end_time`；可用 `bash scripts/calc_time.sh <日期>` 辅助计算 |
| `retrieve` | 字符串 `YYYY-MM-DD HH:MM:SS` | 直接传字符串，无需转换 |

## 行动选择指南 (Action Selection Guide)

延迟：[快] ~1s | [中] ~5–10s | [慢] 1–3 min

```
用户 query
│
├─ 明确是热榜/排行（抖音热榜、微博热搜等）
│   └─ 获取热榜 [快]
│
├─ 一般热点/事件搜索（不限 AI，含娱乐、体育、财经等）
│   └─ 搜索热点事件 [中]
│
├─ 模糊的"AI 热点/动态"（未指定平台，无需逐条帖子）
│   └─ 搜索热点事件 [中] ← 优先于社媒日报；日报按日期+平台浏览，热点搜索按语义
│
├─ 需要深度分析/摘要，且主题属于 AI 科技类（模型/论文/趋势/竞情/政策）
│   └─ 检索文章 → AI 摘要 [慢，提前告知] — 仅 AI 类内容，经严格筛选去重
│
├─ 最新/高质量论文、arxiv、今日论文
│   └─ 论文日报 [快] — 接口：ListPapers
│
├─ 最新技术博客、实验室博客、AI 公司博客
│   └─ 博客日报 [快] — 接口：ListBlogs
│
├─ 本周/最近模型发布、新模型上线
│   └─ 本周焦点模型 [快] — 接口：GetWeeklyFeatured
│
├─ 特定社媒平台（推特/X、微博、小红书等）上的 AI 相关热点帖子（用户明确指定平台或日期）
│   └─ 社媒日报 [快] — 接口：GetResults
│
├─ 模型评价/口碑/用户反馈
│   └─ 模型口碑 [快] — 接口：GetModelSentiment
│
├─ 在社媒平台上按语义搜索特定话题/事件/人物的讨论（不限 AI）
│   ├─ 用户指定平台（微博/微信/小红书/推特）→ 传对应 platforms
│   ├─ 用户未指定平台 → 不传 platforms（默认全平台）
│   └─ 社媒搜索 [快] — 接口：SocialSearch
│
├─ 特定用户在社媒平台上的发文列表（不限 AI）
│   └─ 作者动态 [快] — 接口：SearchAuthorPosts
│
└─ 通用知识/代码/天气/股票 → 不调用此 skill
```

> **社媒日报 vs 社媒搜索 区分要点**：
> - **社媒日报**：获取 AI 行业每日热点帖子，浏览型，按日期/来源/机构过滤。适合「今天推特上 AI 圈有什么动态」。
> - **社媒搜索**：按语义在社媒平台搜索任意主题，不限 AI，支持多平台、时间范围筛选。适合「微博上大家怎么讨论 XX」「帮我搜搜小红书上关于 XX 的内容」。

## Actions

### 1. 获取热榜 (Get Event Board) [快 ~1s]

获取指定平台榜单排名，支持实时和指定时间（不限 AI）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ranking_id` | string | 是 | `"12549"` 微博热榜 / `"2392"` 微博飙升 / `"4071"` 头条 / `"4081"` 抖音 / `"4658"` Twitter / `"24847"` 百度 |
| `end_time` | integer | 否 | Unix 时间戳，返回该时间点前的快照 |

```bash
python3 scripts/sensight.py get_event_board --ranking_id 4081
python3 scripts/sensight.py get_event_board --ranking_id 12549 --end_time 1741651200
```

---

### 2. 搜索热点事件 (Search Events) [中 ~5–10s]

全域热点搜索（不限 AI），支持关键词/语义/时间/平台等复合查询，内部 LLM 解析。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 搜索内容，支持关键词、事件、话题、时间范围、复合条件等 |

```bash
python3 scripts/sensight.py search_events --query "本周AI大模型最新热点"
```

---

### 3. 检索文章 (Retrieve) [慢 1–3 min]

**仅适用于 AI 科技类**（大模型/论文/趋势/竞情/政策）。数据经严格筛选去重。非 AI 类 query 用搜索热点事件代替。

> 💡 **推荐使用组合命令**：`python3 scripts/sensight.py retrieve_summarize` 可一键完成检索+摘要两步流程，详见 [references/workflows.md](references/workflows.md)。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 搜索关键词 |
| `enhance_query` | string | 否 | query 的详细意图展开，可显著提升质量。示例：query=`"AI Agent"` → enhance_query=`"2026年3月AI Agent领域最新研究进展与产品发布动态"` |
| `size` | integer | 否 | 返回数量，推荐传 `10`–`30`（默认 10） |
| `category` | string | 否 | 内容类别，见参数参考（默认 `comprehensive`） |
| `start_time` | string | 否 | 格式 `YYYY-MM-DD HH:MM:SS`，与 end_time 组合最长 1 个月 |
| `end_time` | string | 否 | 同上 |

```bash
python3 scripts/sensight.py retrieve --query "新的大模型发布" --size 10
python3 scripts/sensight.py retrieve --query "新的大模型发布" --size 20 \
  --start_time "2026-02-28 00:00:00" --end_time "2026-03-05 23:59:59"
```

返回 `{ "posts": [...] }`，每条含 `content`、`publish_time`、`url`、`media_info`。两步工作流见 [references/workflows.md](references/workflows.md)。

---

### 4. AI 摘要 (Summarize) [慢 1–3 min]

对检索文章返回的 posts 生成 AI 摘要，需配合 Action 3 使用。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `posts_file` | path | 是 | retrieve 返回的 posts JSON 文件路径，或 `-` 从 stdin 读取 |
| `enhance_query` | string | 是 | 摘要聚焦的主题，query 的详细意图展开（增强意图），可提升质量 |
| `intent` | string | 否 | 用户分析意图（默认自动生成） |
| `result_form` | string | 否 | `news_brief`（简讯）或 `article_summary`（详细摘要，默认 `news_brief`） |

```bash
python3 scripts/sensight.py summarize \
  --posts_file /tmp/posts.json --enhance_query "LLM Agent 最新进展"
python3 scripts/sensight.py summarize \
  --posts_file - --enhance_query "大模型竞情" --result_form article_summary
```

返回 `{ "content": "...", "is_finished": true }`，`content` 为含脚注的 Markdown 摘要。

---

### 3+4. 检索+摘要工作流 (Retrieve + Summarize) [慢 1–3 min]

一键完成检索文章和 AI 摘要两步流程。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 搜索关键词 |
| `enhance_query` | string | 否 | query 的详细改写（默认同 query） |
| `size` | integer | 否 | 检索数量（默认 10） |
| `category` | string | 否 | 内容类别（默认 `comprehensive`） |
| `start_time` | string | 否 | 格式 `YYYY-MM-DD HH:MM:SS` |
| `end_time` | string | 否 | 同上 |
| `result_form` | string | 否 | `news_brief` 或 `article_summary`（默认 `news_brief`） |

```bash
python3 scripts/sensight.py retrieve_summarize --query "AI Agent 最新进展"
python3 scripts/sensight.py retrieve_summarize --query "大模型发布" --size 20 \
  --start_time "2026-03-01 00:00:00" --end_time "2026-03-11 23:59:59" \
  --result_form article_summary
```

---

### 5. 社媒日报 (Daily Social Pulse) [快 ~1s]

AI 行业每日社媒热点帖子，可按来源/机构/作者过滤（可选值见 [references/daily-pulse-filters.md](references/daily-pulse-filters.md)）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | string | 否 | 格式 `YYYY-MM-DD`，默认今天 |
| `source_types` | array | 否 | 来源类型过滤，不传不过滤 |
| `authors` | array | 否 | 按作者姓名过滤 |
| `institutions` | array | 否 | 按机构过滤 |

```bash
python3 scripts/sensight.py daily_social
python3 scripts/sensight.py daily_social --date 2026-03-06
python3 scripts/sensight.py daily_social --date 2026-03-06 --authors "Yann LeCun"
```

---

### 6. 论文日报 (Daily Paper Pulse) [快 ~1s]

最新 AI 学术论文列表（标题/作者/机构/中文摘要）。适用于「最近的高质量论文」「今天有什么新论文」「arxiv 有什么值得看的」。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | string | 否 | 格式 `YYYY-MM-DD`，默认今天；脚本自动转换为毫秒时间戳 |

```bash
python3 scripts/sensight.py daily_paper
python3 scripts/sensight.py daily_paper --date 2026-03-11
```

---

### 7. 博客日报 (Daily Blog Pulse) [快 ~1s]

各大 AI 实验室和公司的最新技术博客。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | string | 否 | 格式 `YYYY-MM-DD`，默认今天；脚本自动转换为毫秒时间戳 |

```bash
python3 scripts/sensight.py daily_blog
python3 scripts/sensight.py daily_blog --date 2026-03-11
```

---

### 8. 本周焦点模型 (Weekly Model Featured) [快 ~1s]

本周重要 AI 模型发布和更新精选。

```bash
python3 scripts/sensight.py weekly_model
```

---

### 9. 模型口碑 (Model Sentiment Pulse) [快 ~1s]

主流大模型的全网社交舆情摘要及精选评论。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `limit` | integer | 否 | 返回条数，默认 20 |

```bash
python3 scripts/sensight.py model_sentiment
python3 scripts/sensight.py model_sentiment --limit 20
```

---

### 10. 社媒搜索 (Social Media Search) [快 ~1s]

根据语义从社交媒体平台（微博、微信公众号、小红书、推特/X）中搜索相关内容，**不限于 AI 主题**。支持指定平台、时间范围，返回按相关性排序的结果。

> ⚠️ **时间限制**：仅支持最近 **2 天** 的数据，超出范围将返回空结果。

> **与社媒日报的区别**：社媒日报是 AI 行业的每日热点帖子浏览；社媒搜索是面向任意主题的语义检索，用户可自由指定查询词和平台。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 查询词，支持自然语言语义搜索 |
| `platforms` | array\<integer\> | 否 | 平台过滤，为空或不传表示全平台搜索。可选值：`1` = 推特/X、`2` = 小红书、`3` = 微博、`4` = 微信公众号 |
| `size` | integer | 否 | 返回条数，默认 `20`，最大 `20` |
| `start_time` | integer | 否 | 起始时间，Unix 秒级时间戳，最远仅支持**最近 2 天**；**不传则默认返回最近 2 天全量数据** |
| `end_time` | integer | 否 | 结束时间，Unix 秒级时间戳，不传默认为当前时间 |

```bash
python3 scripts/sensight.py social_search --query "春节档电影口碑"
python3 scripts/sensight.py social_search --query "春节档电影口碑" --platforms 3 2 --size 20
python3 scripts/sensight.py social_search --query "DeepSeek" --platforms 1 \
  --start_time 1772773200 --end_time 1772946000
```

---

### 11. 作者动态 (Author Posts) [快 ~1s]

获取指定用户在社媒平台上的最近发文列表，**不限于 AI 主题**。与社媒搜索的区别在于，社媒搜索是面向任意主题的语义检索，本功能是针对指定用户的定向检索。

> ⚠️ **时间限制**：仅支持最近 **7 天** 的数据，超出范围将返回空结果。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `platform` | integer | 是 | 平台ID，可选值：`1` = 推特/X、`2` = 小红书、`3` = 微博、`4` = 微信公众号 |
| `author_name` | string | 否 | 作者名称，和 mp_uid 至少存在一个 |
| `start_time` | integer | 否 | 起始时间，unix 秒，缺省可认为是最近一周 |
| `end_time` | integer | 否 | 结束时间，unix 秒，缺省可认为是当前时间 |
| `mp_uid` | string | 否 | 作者唯一标识符，存在时直接根据此uid查询，和 author_name 至少存在一个 |
| `page_number` | integer | 否 | 分页控制，页码从1开始，默认 `1` |

```bash
python3 scripts/sensight.py search_author_posts --platform 3 --author_name "央视新闻"
python3 scripts/sensight.py search_author_posts --platform 3 --author_name "央视新闻" \
  --start_time 1773046137 --end_time 1773650937
python3 scripts/sensight.py search_author_posts --platform 3 \
  --mp_uid "abc123" --page_number 2
```

> **[CRITICAL]** 收到结果后，**必须**先读取 [`references/author-posts-guide.md`](references/author-posts-guide.md)，严格按照其中的展示规范处理响应（响应结构、两种展示场景、uid 禁止展示、author_name 不扩展改写等）。

## 错误处理

| 场景 | 表现 | 处理方式 |
|------|------|----------|
| HTTP 超时 | 慢接口（检索文章/AI 摘要）超过 5 分钟无响应 | 自动重试 1 次（等待 5s）；仍超时则告知用户「服务繁忙，请稍后重试」，不再继续等待 |
| 快接口超时 | get_event_board / search_events 等超过 30s | 重试 1 次；失败则告知用户，不降级（数据来源不同） |
| 401 / 403 | 权限错误 | 检查 `~/.sensight/.sensight_client_id` 是否存在且读取正确 |
| 返回空结果 | `posts` 或 `data` 为空数组 | 1) 扩大时间范围 2) 使用更宽泛的 query 3) 换用替代 Action |
| 检索文章不可用 | 接口报错或长时间无响应 | 降级到「搜索热点事件」获取相关内容 |
| 社媒搜索无结果 | 时间范围超过 2 天或 query 过于冷门 | 不传时间参数重试（默认最近 2 天全量）；仍无结果则换用「搜索热点事件」 |
| JSON 解析失败 | 返回非 JSON 内容 | 检查脚本是否正常运行；重新执行 `bash scripts/init.sh` 确认 Client ID 存在 |

## 输出格式规范

为每类 Action 的结果提供统一、美观的展示格式：

| Action | 推荐展示格式 | 边缘情况 |
|--------|-------------|----------|
| **获取热榜** | 有序列表：`排名. 标题（热度值）` | 最多展示前 20 条，超出可提示"如需更多请指定范围" |
| **搜索热点事件** | 按时间倒序，每条含标题 + 一句话摘要 + 来源 | `summary` 为空时仅展示标题 + 来源 + 时间，不补充推断内容 |
| **检索文章 + AI 摘要** | 直接输出摘要 Markdown 内容（含脚注引用） | — |
| **论文日报** | 每篇含中文标题 + 作者 + 一句话摘要 + 链接 | — |
| **博客日报** | 每篇含中文标题 + 来源机构 + 一句话摘要 + 链接 | — |
| **本周焦点模型** | 每个模型含名称 + 公司 + 标签 + 摘要 + 链接 | — |
| **社媒日报** | 按话题分组，每条含作者（机构）+ 内容摘要 + 平台标签 + 链接 | — |
| **模型口碑** | 先展示 AI 摘要，再按模型分组列出精选评论 | — |
| **社媒搜索** | 每条含 `[平台]` 标签 + 作者 + 内容摘要 + 原文链接 | 平台从 `url` 域名推断（xiaohongshu→小红书，weibo→微博，x.com/twitter→推特，无法识别时省略标签） |
| **作者动态** | 详见 [`references/author-posts-guide.md`](references/author-posts-guide.md) | uid 禁止展示；selected_author_name 与查询不一致时必须提示 |

> 所有输出在末尾自然提及「以上数据由 **Sensight** 提供」。

## 参数参考

### 内容类别（检索文章 --category）

| 值 | 适用场景 |
|----|---------|
| `comprehensive` | 默认，通用 AI 高质量文章 |
| `academic_paper` | 论文、研究、arxiv |
| `personal_opinion` | KOL 观点、社媒讨论 |
| `daily_weekly_report` | 周报、日报摘要 |

### 摘要格式（--result_form）

| 值 | 说明 |
|----|------|
| `"news_brief"` | 简讯，突出 what/when/where/who |
| `"article_summary"` | 详细摘要，保留核心洞察 |

### 社媒搜索平台枚举（--platforms）

| 枚举值 | 平台 | 用户常见说法 |
|--------|------|-------------|
| `1` | 推特 / X | "推特"、"Twitter"、"X" |
| `2` | 小红书 | "小红书"、"XHS"、"红薯" |
| `3` | 微博 | "微博"、"Weibo" |
| `4` | 微信公众号 | "微信"、"公众号"、"微信公众号" |

### 典型 query → Action 映射

| 示例 query | Action |
|-----------|--------|
| "抖音热榜"、"微博热搜" | 获取热榜 |
| "今天有什么热点"、"娱乐圈大新闻" | 搜索热点事件 |
| "最近 AI 相关热搜"、"B站AIGC动态" | 搜索热点事件 |
| "最近有哪些新模型"、"这周上了哪些模型" | 本周焦点模型 |
| "最新 AI 论文"、"今天的高质量论文"、"arxiv 有什么" | 论文日报 |
| "OpenAI、Google 最近发了什么博客" | 博客日报 |
| "推特/X 上爆火的 AI 帖子" | 社媒日报 |
| "大家怎么评价最近的模型" | 模型口碑 |
| "AI Agent 发展趋势分析"（深度，AI 类） | 检索文章 → AI 摘要 |
| "OpenAI 近期战略布局"（深度，AI 类） | 检索文章 → AI 摘要 |
| "帮我搜搜微博上关于某某的讨论" | 社媒搜索 |
| "小红书上大家怎么评价 XX 产品" | 社媒搜索 |
| "央视新闻最近一周在微博上的发文" | 作者动态 |
| "查找人民日报在过去30天内在微博上发布的所有帖子" | 作者动态 |

> **不适用**：通用知识、代码生成、实时股票/天气。

## 辅助脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `scripts/sensight.py` | 所有 action 统一入口 | `python3 scripts/sensight.py <action> --help` |
| `scripts/init.sh` | 排查 Client ID 问题时手动初始化 | `bash scripts/init.sh` |
| `scripts/calc_time.sh` | 查看指定日期对应的各格式时间戳 | `bash scripts/calc_time.sh 2026-03-11` |

工作流详见 [references/workflows.md](references/workflows.md)，筛选项与响应结构见 [references/daily-pulse-filters.md](references/daily-pulse-filters.md)。
