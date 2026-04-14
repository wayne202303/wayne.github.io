#!/usr/bin/env python3
# Sensight Skill — 单一入口脚本
#
# 用法:
#   python3 scripts/sensight.py <action> [选项]
#   python3 scripts/sensight.py --help
#
# 示例:
#   python3 scripts/sensight.py get_event_board --ranking_id 4081
#   python3 scripts/sensight.py search_events --query "AI 热点"
#   python3 scripts/sensight.py daily_paper --date 2026-03-17
#   python3 scripts/sensight.py social_search --query "春节档电影" --platforms 3 2
#   python3 scripts/sensight.py retrieve_summarize --query "AI Agent 进展" --size 20
#   python3 scripts/sensight.py search_author_posts --platform 3 --author_name "央视新闻"

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ModuleNotFoundError:
    requests = None

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

SKILL_VERSION = "0.3.1"
CLIENT_ID_FILE = Path.home() / ".sensight" / ".sensight_client_id"

BASE_SENSIGHT = "https://sensight.bytedance.net"
PPE_ENV = "ppe_sensight_dev"


# ---------------------------------------------------------------------------
# Client ID
# ---------------------------------------------------------------------------


def get_client_id() -> str:
    if CLIENT_ID_FILE.exists():
        return CLIENT_ID_FILE.read_text().strip()
    CLIENT_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_id = str(uuid.uuid4())
    CLIENT_ID_FILE.write_text(new_id)
    print(f"⚙️  已生成新 Client ID: {new_id}", file=sys.stderr)
    return new_id


# ---------------------------------------------------------------------------
# 时间计算
# ---------------------------------------------------------------------------


def calc_time(date_str: str) -> dict:
    """将 YYYY-MM-DD 转换为三种时间格式。"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    # macOS / Linux 兼容：用 UTC 偏移手动计算，但 Sensight 数据为北京时间
    # 此处按本地时间处理（与 calc_time.sh 行为一致）
    start_unix = int(dt.replace(hour=0, minute=0, second=0).timestamp())
    end_unix = start_unix + 86399
    return {
        "start_ms": start_unix * 1000,
        "end_ms": end_unix * 1000,
        "start_unix": start_unix,
        "end_unix": end_unix,
        "start_fmt": f"{date_str} 00:00:00",
        "end_fmt": f"{date_str} 23:59:59",
    }


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# HTTP 工具
# ---------------------------------------------------------------------------


def build_headers(action: str, ppe: bool = False) -> dict:
    client_id = get_client_id()
    headers = {
        "Content-Type": "application/json",
        "x-skill-version": SKILL_VERSION,
        "x-skill-action": action,
        "x-skill-client-id": client_id,
    }
    if False:
        headers["x-use-ppe"] = "1"
        headers["x-tt-env"] = PPE_ENV

    return headers


def post(
    url: str, payload: dict, action: str, ppe: bool = False, timeout: int = 30
) -> dict:
    if requests is None:
        print(
            "缺少依赖 requests，请先安装：python3 -m pip install requests",
            file=sys.stderr,
        )
        sys.exit(1)

    headers = build_headers(action, ppe=ppe)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        resp = requests.post(url, data=body, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout:
        print(f"请求超时（>{timeout}s）", file=sys.stderr)
        if action in ("retrieve", "summarize"):
            print(
                "建议：服务繁忙，请稍后重试；或使用 search_events 获取相关内容",
                file=sys.stderr,
            )
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"网络错误: {e}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code == 401:
        raw = resp.text or ""
        if not raw:
            try:
                raw = resp.content.decode("utf-8", errors="replace")
            except Exception:
                raw = ""
        if raw:
            print(raw, file=sys.stderr)
        else:
            print(f"HTTP 错误 {resp.status_code}: {resp.reason}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code >= 400:
        print(f"HTTP 错误 {resp.status_code}: {resp.reason}", file=sys.stderr)
        if resp.status_code == 403:
            print(
                "建议：检查 ~/.sensight/.sensight_client_id 是否存在，或运行 `bash scripts/init.sh` 重新初始化",
                file=sys.stderr,
            )
        elif resp.status_code >= 500:
            print(
                "建议：服务端错误，稍后重试；若为 retrieve/summarize，可降级使用 search_events",
                file=sys.stderr,
            )
        sys.exit(1)

    raw = resp.text or ""
    if not raw:
        try:
            raw = resp.content.decode("utf-8", errors="replace")
        except Exception:
            raw = ""

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"JSON 解析失败，原始响应：\n{raw[:500]}", file=sys.stderr)
        print(
            "建议：重新运行 `bash scripts/init.sh` 确认 Client ID 正常", file=sys.stderr
        )
        sys.exit(1)


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Action 实现
# ---------------------------------------------------------------------------


def cmd_get_event_board(args):
    payload = {"ranking_id": args.ranking_id}
    if args.end_time:
        payload["end_time"] = args.end_time
    result = post(
        f"{BASE_SENSIGHT}/sensight/skill_get_event_board", payload, "get_event_board"
    )
    print_json(result)


def cmd_search_events(args):
    payload = {"query": args.query}
    result = post(
        f"{BASE_SENSIGHT}/sensight/skill_search_events", payload, "search_events"
    )
    print_json(result)


def cmd_retrieve(args):
    payload = {
        "query": args.query,
        "enhance_query": args.enhance_query or args.query,
        "size": args.size,
        "semantic_rule": {"content_categories": [args.category]},
        "biz_info": {"name": "owls", "type": 0},
    }
    if args.start_time:
        payload["start_time"] = args.start_time
    if args.end_time:
        payload["end_time"] = args.end_time
    print("📥 检索文章中（预计 1–3 分钟）...", file=sys.stderr)
    result = post(
        f"{BASE_SENSIGHT}/sensight/skill_retrieve_posts",
        payload,
        "retrieve",
        ppe=True,
        timeout=300,
    )
    print_json(result)


def cmd_summarize(args):
    if args.posts_file == "-":
        posts = json.load(sys.stdin)
    else:
        with open(args.posts_file) as f:
            posts = json.load(f)
    payload = {
        "posts": posts,
        "enhance_query": args.enhance_query,
        "content_analysis": {
            "intent": args.intent or f"了解{args.enhance_query}相关动态"
        },
        "result_form": args.result_form,
        "biz_info": {"name": "owls", "type": 0},
    }
    print("📝 生成 AI 摘要中（预计 1–3 分钟）...", file=sys.stderr)
    result = post(
        f"{BASE_SENSIGHT}/sensight/skill_summarize_posts",
        payload,
        "summarize",
        ppe=True,
        timeout=300,
    )
    print_json(result)


def cmd_retrieve_summarize(args):
    # 第一步：检索
    retrieve_payload = {
        "query": args.query,
        "enhance_query": args.enhance_query or args.query,
        "size": args.size,
        "semantic_rule": {"content_categories": [args.category]},
        "biz_info": {"name": "owls", "type": 0},
    }
    if args.start_time:
        retrieve_payload["start_time"] = args.start_time
    if args.end_time:
        retrieve_payload["end_time"] = args.end_time

    print(f"📥 第一步：检索文章 (query: {args.query})...", file=sys.stderr)
    retrieve_result = post(
        f"{BASE_SENSIGHT}/sensight/skill_retrieve_posts",
        retrieve_payload,
        "retrieve",
        ppe=True,
        timeout=300,
    )
    posts = retrieve_result.get("posts", [])
    if not posts:
        print("⚠️  检索结果为空，请尝试扩大时间范围或更换关键词", file=sys.stderr)
        sys.exit(1)
    print(f"✅ 检索到 {len(posts)} 篇文章", file=sys.stderr)

    # 第二步：摘要
    summarize_payload = {
        "posts": posts,
        "enhance_query": args.enhance_query or args.query,
        "content_analysis": {"intent": args.intent or f"了解{args.query}相关动态"},
        "result_form": args.result_form,
        "biz_info": {"name": "owls", "type": 0},
    }
    print(
        f"📝 第二步：生成 AI 摘要 (result_form: {args.result_form})...", file=sys.stderr
    )
    summarize_result = post(
        f"{BASE_SENSIGHT}/sensight/skill_summarize_posts",
        summarize_payload,
        "summarize",
        ppe=True,
        timeout=300,
    )
    print_json(summarize_result)
    print("\n✅ 完成", file=sys.stderr)


def cmd_daily_social(args):
    payload = {
        "task_id": 1,
        "date": args.date or today_str(),
        "source_types": args.source_types or [],
        "authors": args.authors or [],
        "institutions": args.institutions or [],
    }
    result = post(
        f"{BASE_SENSIGHT}/sensight/skill_daily_social", payload, "daily_social"
    )
    print_json(result)


def cmd_daily_paper(args):
    date = args.date or today_str()
    t = calc_time(date)
    payload = {"task_id": 1, "start_time": t["start_ms"], "end_time": t["end_ms"]}
    result = post(f"{BASE_SENSIGHT}/sensight/skill_daily_paper", payload, "daily_paper")
    print_json(result)


def cmd_daily_blog(args):
    date = args.date or today_str()
    t = calc_time(date)
    payload = {"task_id": 1, "start_time": t["start_ms"], "end_time": t["end_ms"]}
    result = post(f"{BASE_SENSIGHT}/sensight/skill_daily_blog", payload, "daily_blog")
    print_json(result)


def cmd_weekly_model(args):
    result = post(f"{BASE_SENSIGHT}/sensight/skill_weekly_model", {}, "weekly_model")
    print_json(result)


def cmd_model_sentiment(args):
    payload = {}
    if args.limit:
        payload["limit"] = args.limit
    result = post(
        f"{BASE_SENSIGHT}/sensight/skill_model_sentiment", payload, "model_sentiment"
    )
    print_json(result)


def cmd_social_search(args):
    payload = {"query": args.query}
    if args.platforms:
        payload["platforms"] = args.platforms
    if args.size:
        payload["size"] = args.size
    if args.start_time:
        payload["start_time"] = args.start_time
    if args.end_time:
        payload["end_time"] = args.end_time
    result = post(
        f"{BASE_SENSIGHT}/sensight/skill_social_search",
        payload,
        "social_search",
    )
    print_json(result)


def cmd_search_author_posts(args):
    payload = {"platform": args.platform}
    if args.author_name:
        payload["author_name"] = args.author_name
    if args.mp_uid:
        payload["mp_uid"] = args.mp_uid
    if args.start_time:
        payload["start_time"] = args.start_time
    if args.end_time:
        payload["end_time"] = args.end_time
    if args.size:
        payload["size"] = args.size
    if args.page_number is not None:
        payload["page_number"] = args.page_number
    result = post(
        f"{BASE_SENSIGHT}/sensight/skill_search_author_posts",
        payload,
        "search_author_posts",
    )
    print_json(result)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        prog="sensight.py",
        description="Sensight Skill — 单一入口脚本，封装所有 API action",
    )
    sub = parser.add_subparsers(dest="action", metavar="<action>", required=True)

    # get_event_board
    p = sub.add_parser("get_event_board", help="获取热榜 [快 ~1s]")
    p.add_argument(
        "--ranking_id",
        required=True,
        help="榜单ID: 12549=微博热榜 2392=微博飙升 4071=头条 4081=抖音 4658=Twitter 24847=百度",
    )
    p.add_argument("--end_time", type=int, help="Unix 时间戳，返回该时间点前的快照")
    p.set_defaults(func=cmd_get_event_board)

    # search_events
    p = sub.add_parser("search_events", help="搜索热点事件 [中 ~5–10s]")
    p.add_argument(
        "--query",
        required=True,
        help="搜索内容，支持时间范围/关键词/事件/话题/复合条件",
    )
    p.set_defaults(func=cmd_search_events)

    # retrieve
    p = sub.add_parser("retrieve", help="检索文章（仅 AI 类）[慢 1–3 min]")
    p.add_argument("--query", required=True, help="搜索关键词")
    p.add_argument(
        "--enhance_query", help="query 的详细改写，可提升质量（默认同 query）"
    )
    p.add_argument(
        "--size", type=int, default=10, help="返回数量（推荐 10–30，默认 10）"
    )
    p.add_argument(
        "--category",
        default="comprehensive",
        choices=[
            "comprehensive",
            "academic_paper",
            "personal_opinion",
            "daily_weekly_report",
        ],
        help="内容类别（默认 comprehensive）",
    )
    p.add_argument("--start_time", help='起始时间，格式 "YYYY-MM-DD HH:MM:SS"')
    p.add_argument("--end_time", help='结束时间，格式 "YYYY-MM-DD HH:MM:SS"')
    p.set_defaults(func=cmd_retrieve)

    # summarize
    p = sub.add_parser("summarize", help="AI 摘要（需配合 retrieve 结果）[慢 1–3 min]")
    p.add_argument(
        "--posts_file",
        required=True,
        help="retrieve 返回的 posts JSON 文件路径，或 - 从 stdin 读取",
    )
    p.add_argument("--enhance_query", required=True, help="摘要聚焦的主题")
    p.add_argument("--intent", help="用户分析意图（默认自动生成）")
    p.add_argument(
        "--result_form",
        default="news_brief",
        choices=["news_brief", "article_summary"],
        help="摘要格式（默认 news_brief）",
    )
    p.set_defaults(func=cmd_summarize)

    # retrieve_summarize
    p = sub.add_parser(
        "retrieve_summarize", help="检索文章 + AI 摘要 两步工作流 [慢 1–3 min]"
    )
    p.add_argument("--query", required=True, help="搜索关键词")
    p.add_argument("--enhance_query", help="query 的详细改写（默认同 query）")
    p.add_argument("--size", type=int, default=10, help="检索数量（默认 10）")
    p.add_argument(
        "--category",
        default="comprehensive",
        choices=[
            "comprehensive",
            "academic_paper",
            "personal_opinion",
            "daily_weekly_report",
        ],
        help="内容类别（默认 comprehensive）",
    )
    p.add_argument("--start_time", help='起始时间，格式 "YYYY-MM-DD HH:MM:SS"')
    p.add_argument("--end_time", help='结束时间，格式 "YYYY-MM-DD HH:MM:SS"')
    p.add_argument("--intent", help="用户分析意图（默认自动生成）")
    p.add_argument(
        "--result_form",
        default="news_brief",
        choices=["news_brief", "article_summary"],
        help="摘要格式（默认 news_brief）",
    )
    p.set_defaults(func=cmd_retrieve_summarize)

    # daily_social
    p = sub.add_parser("daily_social", help="AI 行业社媒日报 [快 ~1s]")
    p.add_argument("--date", help="日期 YYYY-MM-DD（默认今天）")
    p.add_argument("--source_types", nargs="*", help="来源类型过滤")
    p.add_argument("--authors", nargs="*", help="按作者姓名过滤")
    p.add_argument("--institutions", nargs="*", help="按机构过滤")
    p.set_defaults(func=cmd_daily_social)

    # daily_paper
    p = sub.add_parser("daily_paper", help="AI 论文日报 [快 ~1s]")
    p.add_argument("--date", help="日期 YYYY-MM-DD（默认今天）")
    p.set_defaults(func=cmd_daily_paper)

    # daily_blog
    p = sub.add_parser("daily_blog", help="AI 博客日报 [快 ~1s]")
    p.add_argument("--date", help="日期 YYYY-MM-DD（默认今天）")
    p.set_defaults(func=cmd_daily_blog)

    # weekly_model
    p = sub.add_parser("weekly_model", help="本周焦点模型 [快 ~1s]")
    p.set_defaults(func=cmd_weekly_model)

    # model_sentiment
    p = sub.add_parser("model_sentiment", help="模型口碑 [快 ~1s]")
    p.add_argument("--limit", type=int, default=20, help="返回条数（默认 20）")
    p.set_defaults(func=cmd_model_sentiment)

    # social_search
    p = sub.add_parser("social_search", help="社媒语义搜索（最近 2 天）[快 ~1s]")
    p.add_argument("--query", required=True, help="查询词，支持自然语言语义搜索")
    p.add_argument(
        "--platforms",
        nargs="*",
        type=int,
        help="平台过滤（可多选）: 1=推特/X 2=小红书 3=微博 4=微信公众号；不传则全平台",
    )
    p.add_argument("--size", type=int, help="返回条数（默认 20，最大 20）")
    p.add_argument(
        "--start_time", type=int, help="起始时间，Unix 秒级时间戳（最远 2 天前）"
    )
    p.add_argument("--end_time", type=int, help="结束时间，Unix 秒级时间戳（默认当前）")
    p.set_defaults(func=cmd_social_search)

    # search_author_posts
    p = sub.add_parser(
        "search_author_posts", help="作者动态（指定用户发文列表）[快 ~1s]"
    )
    p.add_argument(
        "--platform",
        required=True,
        type=int,
        help="平台ID: 1=推特/X 2=小红书 3=微博 4=微信公众号",
    )
    p.add_argument("--author_name", help="作者名称（与 --mp_uid 至少传一个）")
    p.add_argument("--mp_uid", help="作者唯一标识符（优先于 author_name）")
    p.add_argument("--start_time", type=int, help="起始时间，Unix 秒（缺省约最近一周）")
    p.add_argument("--end_time", type=int, help="结束时间，Unix 秒（缺省当前时间）")
    p.add_argument("--size", type=int, help="返回条数（用户未指定时不传）")
    p.add_argument(
        "--page_number", type=int, default=1, help="页码，从 1 开始（默认 1）"
    )
    p.set_defaults(func=cmd_search_author_posts)

    args = parser.parse_args()

    # 校验 search_author_posts 需要 author_name 或 mp_uid
    if args.action == "search_author_posts":
        if not args.author_name and not args.mp_uid:
            parser.error("search_author_posts 需要 --author_name 或 --mp_uid 至少一个")

    args.func(args)


if __name__ == "__main__":
    main()
