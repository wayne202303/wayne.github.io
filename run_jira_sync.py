import os
import sys
import subprocess
import json
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
        print(f"[ERROR] Failed to get token: {resp.text}")
        return None
    data = resp.json()
    if data.get("code") != 0:
        print(f"[ERROR] Failed to get token: {data.get('msg')}")
        return None
    return data["tenant_access_token"]


# 给用户发飞书消息
def send_message(open_id, content):
    token = get_feishu_token()
    if not token:
        print("[ERROR] Cannot send message without token")
        return False
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    params = {"receive_id_type": "open_id"}
    data = {
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(url, params=params, json=data, headers=headers, timeout=10)
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get("code") == 0:
            print("[INFO] Message sent successfully")
            return True
        else:
            print(f"[ERROR] Failed to send message: {result.get('msg')}")
            return False
    else:
        print(f"[ERROR] Failed to send message: {resp.status_code} {resp.text}")
        return False


# 执行Jira同步
def run_jira_sync():
    print("[INFO] Starting Jira sync...")
    result = subprocess.run(
        [sys.executable, JIRA_SYNC_SCRIPT_PATH],
        capture_output=True,
        text=True,
        timeout=120
    )
    output = result.stdout + "\n" + result.stderr
    print(output)
    return output


def main():
    print("="*60)
    print("Jira Sync - One Click Version")
    print("="*60)
    print()
    
    # 执行 Jira 同步
    output = run_jira_sync()
    
    # 发送结果到飞书
    print()
    print("[INFO] Sending result to Feishu...")
    success = send_message(MY_OPEN_ID, f"[INFO] Jira sync completed!\n```\n{output}\n```")
    
    if success:
        print("[INFO] Done! Result sent to Feishu.")
    else:
        print("[ERROR] Failed to send result to Feishu.")


if __name__ == "__main__":
    main()
