import os
import sys
import subprocess
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# -------------------------- 配置区 --------------------------
JIRA_SYNC_SCRIPT_PATH = r".agents\skills\jira_to_feishu\scripts\jira_to_feishu.py"
MY_OPEN_ID = "ou_9f5ae70c97a18d67be0c3486d538156a"
# ----------------------------------------------------------

def run_command(cmd):
    """运行飞书 CLI 命令"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    return result.stdout, result.stderr

def send_message(open_id, content):
    """使用飞书 CLI 发送消息"""
    data = {
        "receive_id_type": "open_id",
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }
    
    # 创建临时 JSON 文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f)
        temp_file = f.name
    
    try:
        cmd = f'lark-cli api POST /open-apis/im/v1/messages --data @{temp_file}'
        stdout, stderr = run_command(cmd)
        
        try:
            result = json.loads(stdout)
            if result.get('code') == 0:
                print("[INFO] 消息发送成功")
            else:
                print(f"[ERROR] 消息发送失败：{result.get('msg')}")
        except:
            print(f"[ERROR] 消息发送失败：{stderr}")
    finally:
        os.unlink(temp_file)

def run_jira_sync():
    """执行 Jira 同步"""
    print("[INFO] 正在执行 Jira 同步...")
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
    print("Jira同步工具 - 飞书 CLI 版本")
    print("="*60)
    print("\n请选择操作：")
    print("1. 执行 Jira 同步")
    print("2. 执行 Jira 同步并发送结果到飞书")
    print("3. 测试发送飞书消息")
    print("4. 退出")
    
    while True:
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == "1":
            run_jira_sync()
        
        elif choice == "2":
            print("[INFO] 正在执行 Jira 同步...")
            output = run_jira_sync()
            print("\n[INFO] 正在发送结果到飞书...")
            send_message(MY_OPEN_ID, f"[INFO] Jira同步执行完成！输出结果：\n```\n{output}\n```")
        
        elif choice == "3":
            test_msg = f"测试消息 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            print(f"[INFO] 正在发送测试消息：{test_msg}")
            send_message(MY_OPEN_ID, test_msg)
        
        elif choice == "4":
            print("[INFO] 退出程序")
            break
        
        else:
            print("[ERROR] 无效选项，请重新输入")

if __name__ == "__main__":
    main()
