# 工作流参考

## 文章洞察工作流（检索 + 摘要）

检索文章与 AI 摘要需两步串联。推荐使用 `retrieve_summarize` 一键完成。

```bash
# 基础用法
python3 scripts/sensight.py retrieve_summarize --query "AI Agent 最新进展"

# 完整参数
python3 scripts/sensight.py retrieve_summarize \
  --query "大模型发布" \
  --enhance_query "2026年3月大模型发布与更新动态" \
  --start_time "2026-03-01 00:00:00" \
  --end_time "2026-03-11 23:59:59" \
  --size 20 \
  --result_form article_summary
```

脚本自动处理：Client ID 注入、中间 JSON 在内存传递、空结果提示。

如需分步执行（例如先检索、人工确认后再摘要）：

```bash
# 第一步：检索，结果保存到文件
python3 scripts/sensight.py retrieve --query "大模型发布" --size 10 > /tmp/posts.json

# 第二步：基于检索结果生成摘要
python3 scripts/sensight.py summarize \
  --posts_file /tmp/posts.json \
  --enhance_query "大模型发布动态" \
  --result_form news_brief
```

---

## social_search 时间戳快速参考

`social_search` 的 `--start_time` / `--end_time` 需要秒级 Unix 时间戳，可用：

```bash
bash scripts/calc_time.sh 2026-03-11
# 输出：START_UNIX / END_UNIX 等各格式时间戳
```

筛选项枚举值与各接口响应结构见 [daily-pulse-filters.md](daily-pulse-filters.md)。
