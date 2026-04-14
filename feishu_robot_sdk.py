import os
import sys
import subprocess
import json
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from dotenv import load_dotenv

load_dotenv()

# -------------------------- 配置区 --------------------------
FEISHU_APP_ID = "cli_a95276171379dbda"
FEISHU_APP_SECRET = "weWRebXG3hpUFdHWVTtAKjDY3Vrleyiw"
JIRA_SYNC_SCRIPT_PATH = r".agents\skills\jira_to_feishu\scripts\jira_to_feishu.py"
# ----------------------------------------------------------

def send_reply_message(client: lark.Client, message_id: str, content: str):
    """回复消息"""
    req = ReplyMessageRequest.builder() \
        .message_id(message_id) \
        .request_body(ReplyMessageRequestBody.builder()
            .msg_type("text")
            .content(json.dumps({"text": content}))
            .build()) \
        .build()
    
    resp = client.im.v1.message.reply(req)
    
    if not resp.success():
        print(f"[ERROR] Failed to send message: {resp.code}, {resp.msg}")
        return False
    return True

def process_message_text(text: str, message_id: str):
    """处理消息文本"""
    print(f"[INFO] Message text: {text}")
    
    # 创建客户端用于回复
    client = lark.Client.builder() \
        .app_id(FEISHU_APP_ID) \
        .app_secret(FEISHU_APP_SECRET) \
        .log_level(lark.LogLevel.INFO) \
        .build()
    
    # 处理命令
    text_lower = text.lower()
    
    if "同步jira" in text_lower:
        print("[INFO] Executing Jira sync...")
        
        # 发送开始消息
        send_reply_message(client, message_id, "[INFO] 收到指令，正在执行Jira同步...")
        
        # 执行 Jira 同步
        try:
            result = subprocess.run(
                [sys.executable, JIRA_SYNC_SCRIPT_PATH],
                capture_output=True,
                text=True,
                timeout=120
            )
            output = result.stdout + "\n" + result.stderr
            
            # 发送结果（限制长度，避免消息太长）
            if len(output) > 1000:
                output = output[:1000] + "\n... (output truncated)"
            
            send_reply_message(client, message_id, f"[INFO] Jira同步执行完成！\n```\n{output}\n```")
            print("[INFO] Done! Result sent.")
        except Exception as e:
            error_msg = f"[ERROR] Jira同步执行失败：{str(e)}"
            send_reply_message(client, message_id, error_msg)
            print(error_msg)
    
    elif "你好" in text or "hello" in text_lower:
        send_reply_message(client, message_id, "你好！我是Jira同步机器人，发送「同步Jira」即可执行同步任务。")
    
    else:
        send_reply_message(client, message_id, "你好！我是Jira同步机器人。\n发送「同步Jira」即可执行同步任务。")

def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
    """处理接收消息事件（v2.0版本）"""
    print(f"[INFO] Received v2 message event: {lark.JSON.marshal(data, indent=2)}")
    
    try:
        event = data.event
        message = event.message
        
        # 解析消息内容
        try:
            content = json.loads(message.content)
            text = content.get("text", "").strip()
        except:
            text = ""
        
        process_message_text(text, message.message_id)
    except Exception as e:
        print(f"[ERROR] Error processing v2 message: {str(e)}")

def do_message_event(data: lark.CustomizedEvent) -> None:
    """处理接收消息事件（v1.0版本）"""
    print(f"[INFO] Received v1 message event: {lark.JSON.marshal(data, indent=2)}")
    
    try:
        # 解析 v1.0 版本的消息
        event_data = data.event
        if isinstance(event_data, dict):
            message = event_data.get("message", {})
            message_id = message.get("message_id", "")
            
            # 解析消息内容
            try:
                content = json.loads(message.get("content", "{}"))
                text = content.get("text", "").strip()
            except:
                text = ""
            
            if message_id and text:
                process_message_text(text, message_id)
    except Exception as e:
        print(f"[ERROR] Error processing v1 message: {str(e)}")

def main():
    print("="*60)
    print("Feishu Robot - Jira Sync Bot")
    print("="*60)
    print()
    
    # 创建事件处理器 - 同时支持 v1 和 v2 版本
    event_handler = lark.EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1) \
        .register_p1_customized_event("message", do_message_event) \
        .build()
    
    # 创建长连接客户端
    cli = lark.ws.Client(
        FEISHU_APP_ID,
        FEISHU_APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.DEBUG
    )
    
    print("[INFO] Starting Feishu robot...")
    print("[INFO] Waiting for messages...")
    print("[INFO] Send '同步Jira' to test!")
    print()
    
    # 启动客户端
    cli.start()

if __name__ == "__main__":
    main()
