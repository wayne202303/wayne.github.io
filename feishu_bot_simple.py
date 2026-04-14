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
    resp = requests.post(url, params=params, json=data, headers=headers, timeout=10)
    if resp.status_code == 200:
        print("[INFO] 消息发送成功")
    else:
        print(f"[ERROR] 消息发送失败：{resp.status_code} {resp.text}")


# 执行Jira同步
def run_jira_sync():
    print("[INFO] 正在执行Jira同步...")
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
    print("Jira同步工具 - 简单版本")
    print("="*60)
    print("\n请选择操作：")
    print("1. 执行Jira同步")
    print("2. 执行Jira同步并发送结果到飞书")
    print("3. 退出")
    
    while True:
        choice = input("\n请输入选项 (1-3): ").strip()
        
        if choice == "1":
            run_jira_sync()
        
        elif choice == "2":
            print("[INFO] 正在执行Jira同步...")
            output = run_jira_sync()
            print("\n[INFO] 正在发送结果到飞书...")
            send_message(MY_OPEN_ID, f"[INFO] Jira同步执行完成！输出结果：\n```\n{output}\n```")
        
        elif choice == "3":
            print("[INFO] 退出程序")
            break
        
        else:
            print("[ERROR] 无效选项，请重新输入")


if __name__ == "__main__":
    main()
