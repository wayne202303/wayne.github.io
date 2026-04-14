#!/usr/bin/env bash
# Sensight Skill — 时间戳计算辅助
#
# 用法:
#   bash scripts/calc_time.sh [日期]
#
# 日期格式: YYYY-MM-DD（默认今天）
#
# 输出 4 种格式供不同接口使用:
#   START_MS   — 毫秒时间戳 00:00:00 (ListPapers / ListBlogs)
#   END_MS     — 毫秒时间戳 23:59:59 (ListPapers / ListBlogs)
#   START_UNIX — 秒级时间戳 00:00:00 (社媒搜索 start_time)
#   END_UNIX   — 秒级时间戳 23:59:59 (社媒搜索 end_time)
#   START_FMT  — "YYYY-MM-DD 00:00:00" (检索文章 start_time)
#   END_FMT    — "YYYY-MM-DD 23:59:59" (检索文章 end_time)

set -euo pipefail

DATE="${1:-$(date +%Y-%m-%d)}"

# 兼容 macOS (BSD date) 和 Linux (GNU date)
if date --version &>/dev/null 2>&1; then
  # GNU date (Linux)
  START_UNIX=$(date -d "${DATE} 00:00:00" +%s)
else
  # BSD date (macOS)
  START_UNIX=$(date -j -f "%Y-%m-%d %H:%M:%S" "${DATE} 00:00:00" +%s)
fi

END_UNIX=$((START_UNIX + 86399))
START_MS=$((START_UNIX * 1000))
END_MS=$((END_UNIX * 1000))
START_FMT="${DATE} 00:00:00"
END_FMT="${DATE} 23:59:59"

cat <<EOF
日期: ${DATE}

ListPapers / ListBlogs (毫秒时间戳):
  start_time: ${START_MS}
  end_time:   ${END_MS}

社媒搜索 (秒级时间戳):
  start_time: ${START_UNIX}
  end_time:   ${END_UNIX}

检索文章 (字符串格式):
  start_time: "${START_FMT}"
  end_time:   "${END_FMT}"
EOF
