#!/usr/bin/env bash
# Sensight Skill — 初始化 Client ID
# 幂等：文件已存在则直接读取，不存在则生成新 UUID

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ID_FILE="$HOME/.sensight/.sensight_client_id"

if [ -f "$ID_FILE" ]; then
  cat "$ID_FILE"
else
  if command -v uuidgen &>/dev/null; then
    NEW_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
  elif command -v python3 &>/dev/null; then
    NEW_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
  elif command -v python &>/dev/null; then
    NEW_ID=$(python -c "import uuid; print(uuid.uuid4())")
  else
    echo "ERROR: 无法生成 UUID，请安装 uuidgen 或 python3" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$ID_FILE")"
  echo "$NEW_ID" > "$ID_FILE"
  echo "$NEW_ID"
fi
