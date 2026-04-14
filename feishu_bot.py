import os
import sys
import subprocess
import json
import websocket
import requests
from dotenv import load_dotenv

load_dotenv()

# -------------------------- 配置区 --------------------------
FEISHU_APP_ID = "cli_a95276171379dbda"
FEISHU_APP_SECRET = "weWRebXG3hpUFdHWVTtAKjDY3Vrleyiw"
JIRA_SYNC_SCRIPT_PATH = r".agents\skills\jira_to_feishu\scripts\jira_to_feishu.py"
MY_OPEN_ID = "ou_9f5ae70c97a18d67be0c3486d538156a"
# ----------------------------------------------------------

# 获取飞书token
def get_feishu_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }, timeout=10)
    if resp.status_code != 200:
        print(f"[ERROR] 获取token失败：{resp.text}")
        sys.exit(1)
    data = resp.json()
    if data.get("code") != 0:
        print(f"[ERROR] 获取token返回错误：{data.get('msg')}")
        sys.exit(1)
    return data["tenant_access_token"]


# 给用户发飞书消息
def send_message(open_id, content):
    token = get_feishu_token()
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    params = {"receive_id_type": "open_id"}
    data = {
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }
    headers = {"Authorization": f"Bearer {token}"}
    requests.post(url, params=params, json=data, headers=headers, timeout=10)


# 处理消息
def on_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("type") != "im.message.receive_v1":
            return
        event = data.get("event", {})
        msg = event.get("message", {})
        content = json.loads(msg.get("content", "{}")).get("text", "").strip()
        sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id", "")

        # 只处理你自己发的消息
        if sender_id != MY_OPEN_ID:
            return

        print(f"[INFO] 收到消息：{content} from {sender_id}")

        if "同步Jira" in content:
            send_message(sender_id, "[INFO] 收到指令，正在执行Jira同步...")
            result = subprocess.run(
                [sys.executable, JIRA_SYNC_SCRIPT_PATH],
                capture_output=True,
                text=True,
                timeout=120
            )
            output = result.stdout + "\n" + result.stderr
            send_message(sender_id, f"[INFO] Jira同步执行完成！输出结果：\n```\n{output}\n```")
            print("[INFO] 执行完成，结果已返回")

        elif "查询" in content:
            send_message(sender_id, f"[INFO] 收到查询指令：{content}\n正在查询，请稍候...")
            # 这里可以后续扩展查询功能
            send_message(sender_id, f"[INFO] 查询完成，请查看结果")

    except Exception as e:
        print(f"[ERROR] 处理消息错误：{str(e)}")


def on_error(ws, error):
    print(f"[ERROR] websocket错误：{str(error)}")


def on_close(ws):
    print("[INFO] 连接关闭，重新连接...")


def on_open(ws):
    print("[INFO] 连接成功，正在监听消息...")
    print("[INFO] 现在可以在飞书给机器人发「同步Jira」测试了")


if __name__ == "__main__":
    token = get_feishu_token()
    # 获取长连接endpoint
    resp = requests.get(
        "https://open.feishu.cn/open-apis/gateway/bot/v1/endpoints",
        headers={"Authorization": f"Bearer {token}"}
    )
    if resp.status_code != 200:
        print(f"[ERROR] 获取长连接地址失败：{resp.status_code} {resp.text}")
        sys.exit(1)
    data = resp.json()
    if data.get("code") != 0:
        print(f"[ERROR] 获取长连接地址返回错误：{data.get('msg')}")
        sys.exit(1)
    ws_url = data["data"]["endpoints"][0]
    print(f"[INFO] 正在连接飞书长连接：{ws_url}")

    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        f"{ws_url}?token={token}",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()
