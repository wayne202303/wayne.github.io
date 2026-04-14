import os
import sys
import re
import requests
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# -------------------------- 配置区 --------------------------
# Jira配置
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")

# 飞书配置
FEISHU_APP_ID = "cli_a95276171379dbda"
FEISHU_APP_SECRET = "weWRebXG3hpUFdHWVTtAKjDY3Vrleyiw"
FEISHU_DOC_TOKEN = "shtcnEdGsdXmuVKvxVGAOmpXKwf"
FEISHU_SHEET_ID = "fLpHwq"
# ----------------------------------------------------------

try:
    # 检查必要配置
    if not all([JIRA_BASE_URL, JIRA_TOKEN, FEISHU_APP_ID, FEISHU_APP_SECRET]):
        print("[ERROR] 缺少必要配置，请检查脚本里的 FEISHU_APP_ID 和 FEISHU_APP_SECRET 是否填写正确")
        sys.exit(1)

    # -------------------------- 1. 获取飞书 tenant_access_token --------------------------
    def get_feishu_token():
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={
            "app_id": FEISHU_APP_ID,
            "app_secret": FEISHU_APP_SECRET
        }, timeout=30)
        if resp.status_code != 200:
            print(f"[ERROR] 获取飞书token失败：HTTP {resp.status_code} 响应：{resp.text}")
            sys.exit(1)
        data = resp.json()
        if data.get("code") != 0:
            print(f"[ERROR] 获取飞书token返回错误：code={data.get('code')} msg={data.get('msg')}")
            sys.exit(1)
        return data["tenant_access_token"]

    # -------------------------- 2. 拉取Jira数据 --------------------------
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Accept": "application/json",
    }

    search_url = f"{JIRA_BASE_URL}/rest/api/2/search"

    jql = 'project = MK AND issuetype in ("任务", "优化", "故事") AND status = "测试中" AND NOT summary ~ "loc" AND NOT description ~ "loc"'

    params = {
        "jql": jql,
        "maxResults": 100,
        "fields": "summary,status,assignee,issuetype,fixVersions,updated"
    }

    print("[INFO] 正在拉取Jira数据...")
    resp = requests.get(search_url, headers=headers, params=params, timeout=60)
    if resp.status_code != 200:
        print(f"[ERROR] Jira请求失败：HTTP {resp.status_code} 响应：{resp.text}")
        sys.exit(1)
    data = resp.json()
    issues = data.get("issues", [])
    print(f"[INFO] 拉取完成，共 {len(issues)} 条原始任务")

    # -------------------------- 3. 数据处理、排序、过滤 --------------------------
    def get_sort_key(version_name):
        matches = re.findall(r'(\d{4})', version_name.strip())
        if matches:
            return int(matches[-1])
        return 0

    processed = []
    for issue in issues:
        fields = issue.get("fields", {})
        fix_versions = fields.get("fixVersions") or []
        max_key = 0
        version_text = ""
        if fix_versions:
            for v in fix_versions:
                name = v.get("name", "")
                key = get_sort_key(name)
                if key > max_key:
                    max_key = key
                    version_text = name
            if not version_text:
                version_text = ", ".join(v.get("name", "") for v in fix_versions)
        if "日常资源版本" in version_text:
            continue
        updated_str = fields.get("updated", "")
        updated_ts = 0
        if updated_str:
            try:
                from dateutil.parser import parse
                updated_ts = parse(updated_str).timestamp()
            except:
                pass
        processed.append({
            "version_key": max_key,
            "updated_ts": updated_ts,
            "version": version_text,
            "summary": fields.get("summary", ""),
            "issue_type": (fields.get("issuetype") or {}).get("name", ""),
            "assignee": (fields.get("assignee") or {}).get("displayName", "未分配"),
            "status": (fields.get("status") or {}).get("name", "")
        })
    processed.sort(key=lambda x: (-x["version_key"], -x["updated_ts"]))
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[INFO] 处理完成，过滤后共 {len(processed)} 条有效任务")

    # -------------------------- 4. 追加写入飞书表格 --------------------------
    print("[INFO] 正在获取飞书访问凭证...")
    feishu_token = get_feishu_token()

    # 先查询当前已有行数，定位到末尾
    print("[INFO] 查询表格当前行数...")
    query_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_DOC_TOKEN}/values/{FEISHU_SHEET_ID}!A:A"
    query_resp = requests.get(query_url, headers={"Authorization": f"Bearer {feishu_token}"}, timeout=30)
    if query_resp.status_code != 200:
        print(f"[ERROR] 查询表格行数失败：HTTP {query_resp.status_code} {query_resp.text}")
        sys.exit(1)
    query_data = query_resp.json()
    if query_data.get("code") != 0:
        print(f"[ERROR] 查询表格行数返回错误：code={query_data.get('code')} msg={query_data.get('msg')}")
        sys.exit(1)

    # 构造写入数据
    write_rows = []
    write_rows.append([f"【{today} Jira任务整理】", "", "", "", "", ""])
    write_rows.append(["日期", "版本", "任务类型", "任务描述", "执行人", "任务状态"])
    for item in processed:
        write_rows.append([
            today,
            item["version"],
            item["issue_type"],
            item["summary"],
            item["assignee"],
            item["status"]
        ])
    write_rows.append(["", "", "", "", "", ""])

    # 计算追加位置
    values = query_data["data"].get("values", [])
    start_row = len(values) + 1
    append_range = f"{FEISHU_SHEET_ID}!A{start_row}:F{start_row + len(write_rows) - 1}"

    print(f"[INFO] 正在写入飞书表格，共 {len(processed)} 条记录...")
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_DOC_TOKEN}/values_append"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {feishu_token}"},
        json={
            "valueRange": {
                "range": append_range,
                "values": write_rows
            },
            "options": {
                "insertDataOption": "INSERT_ROWS"
            }
        },
        timeout=120
    )
    print(f"[INFO] 飞书接口返回：status={resp.status_code}, body={resp.text}")
    if resp.status_code != 200:
        print(f"[ERROR] 写入飞书失败：HTTP {resp.status_code}")
        sys.exit(1)
    result = resp.json()
    if result.get("code") != 0:
        print(f"[ERROR] 写入飞书返回错误：code={result.get('code')} msg={result.get('msg')}")
        sys.exit(1)
    print(f"[INFO] 全部完成！成功追加 {len(processed)} 条记录到飞书表格末尾：")
    print(f"https://bytedance.larkoffice.com/sheets/shtcnEdGsdXmuVKvxVGAOmpXKwf?sheet=fLpHwq")
    print("[INFO] 打开表格后，滚动到最底部就能看到今天最新的数据")


except Exception as e:
    print(f"[ERROR] 发生未知错误：{str(e)}")
    print("[INFO] 错误堆栈：")
    print(traceback.format_exc())
