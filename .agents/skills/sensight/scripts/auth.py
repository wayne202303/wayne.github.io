#!/usr/bin/env python3

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, NoReturn, Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen

CLIENT_ID_FILE = Path.home() / ".sensight" / ".sensight_client_id"
AUTH_SERVER_BASE_URL = "https://sensight.bytedance.net"
SKILL_VERSION = "0.3.1"


def exit_with_error(message: str, exit_code: int = 1) -> NoReturn:
    print(message, file=sys.stderr)
    sys.exit(exit_code)


def get_client_id() -> str:
    if CLIENT_ID_FILE.exists():
        return CLIENT_ID_FILE.read_text().strip()
    CLIENT_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_id = str(uuid.uuid4())
    CLIENT_ID_FILE.write_text(new_id)
    return new_id


def _parse_json_object(raw: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        exit_with_error("服务返回非 JSON，无法解析")
    if not isinstance(parsed, dict):
        return {}
    return parsed


def build_headers() -> dict:
    headers = {
        "Content-Type": "application/json",
        # "x-use-ppe": "1",
        # "x-tt-env": "ppe_sensight_dev",
    }

    return headers


def http_post_json(
    url: str, payload: Dict[str, Any], timeout: int = 15
) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode()
    headers = build_headers()
    req = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return _parse_json_object(resp.read().decode())
    except HTTPError as e:
        msg = ""
        try:
            msg = e.read().decode()[:500]
        except Exception:
            msg = ""
        exit_with_error(f"鉴权请求失败（HTTP {e.code}）{(': ' + msg) if msg else ''}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="auth.py",
        description="Sensight 鉴权脚本",
    )
    sub = parser.add_subparsers(dest="action", metavar="<action>", required=True)

    p = sub.add_parser(
        "feishu_user", help="上报飞书用户 union_id 与 client_id 给服务端"
    )
    p.add_argument("--union_id", required=True, help="飞书用户 union_id")
    p = sub.add_parser(
        "email_user", help="上报Aime或者mira用户 email 与 client_id 给服务端"
    )
    p.add_argument("--email", required=False, help="Aime用户 email")

    args = parser.parse_args()
    base_url = AUTH_SERVER_BASE_URL

    client_id = get_client_id()
    if args.action == "feishu_user":
        http_post_json(
            f"{base_url}/sensight/skill_user_auth",
            {"client_id": client_id, "auth_id": args.union_id, "auth_type": "feishu"},
            timeout=15,
        )
    elif args.action == "email_user":
        if not args.email:
            email = os.environ.get("AIME_CURRENT_USER_EMAIL")
        else:
            email = args.email
        if not email:
            exit_with_error("未获取到email, 请手动传递 --email 参数")
        http_post_json(
            f"{base_url}/sensight/skill_user_auth",
            {"client_id": client_id, "auth_id": email, "auth_type": "email"},
            timeout=15,
        )
    else:
        exit_with_error("未知 action")

    print("授权已完成。")


if __name__ == "__main__":
    main()
